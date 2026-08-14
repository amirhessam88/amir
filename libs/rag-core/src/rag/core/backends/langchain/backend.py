"""LangChain LCEL retrieve-and-generate over a strategy-scoped Chroma directory."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Final

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document as LcDocument
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.core.catalog import catalog_from_documents, write_paper_catalog
from rag.core.citations import citations_from_nodes, format_citations
from rag.core.config import RagConfig
from rag.core.index import IndexMissingError
from rag.core.ingest import IngestResult, _reset_collection
from rag.core.loaders import list_pdf_paths, load_pdf_pages
from rag.core.passage import (
    QA_GROUNDING_RULES,
    is_acknowledgement_text,
    is_author_question,
    is_proceedings_boilerplate_text,
    page_from_mapping,
)
from rag.core.query import QueryResult, require_openai_api_key
from rag.core.strategy import RagStrategy
from rag.core.text_quality import is_prose_text

_QA_SYSTEM: Final = (
    "Context from research papers is below. Each excerpt is labeled with "
    "filename and page.\n"
    "---------------------\n"
    "{context}\n"
    "---------------------\n"
    "Answer the question using only this context. Be concise and direct "
    "(a few sentences unless the question needs more). These excerpts are a "
    "retrieved subset — not the full library. Do not say 'all papers' or "
    "'both papers' unless you list every filename you used. If the question "
    "is about the whole corpus, say this context is too narrow. " + QA_GROUNDING_RULES
)


class LangChainBackend:
    """LangChain retriever + ChatOpenAI over a dedicated Chroma persist dir."""

    def ingest(
        self,
        *,
        config: RagConfig,
        rebuild: bool = True,
        embed_model: object | None = None,
    ) -> IngestResult:
        """Chunk, embed, and persist pages with LangChain + Chroma.

        Parameters
        ----------
        config : RagConfig
            Paths, chunking, and model settings.
        rebuild : bool
            When True, delete the existing collection before writing.
        embed_model : object or None
            Unused; LangChain builds HuggingFace embeddings from config.

        Returns
        -------
        IngestResult
            Counts and paths for the run.
        """
        _ = embed_model
        pdf_paths = list_pdf_paths(papers_dir=config.papers_dir)
        pages = load_pdf_pages(pdf_paths=pdf_paths)
        write_paper_catalog(
            catalog=catalog_from_documents(pdf_paths=pdf_paths, documents=pages),
            chroma_dir=config.chroma_dir,
        )
        documents = [
            LcDocument(page_content=page.text, metadata=dict(page.metadata)) for page in pages
        ]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )
        splits = splitter.split_documents(documents=documents)
        if rebuild:
            _reset_collection(config=config)
        else:
            config.ensure_dirs()
        embeddings = HuggingFaceEmbeddings(model_name=config.embed_model_name)
        Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=str(config.chroma_dir),
            collection_name=config.collection_name,
        )
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        collection = client.get_or_create_collection(name=config.collection_name)
        return IngestResult(
            documents=len(documents),
            nodes=int(collection.count()),
            chroma_dir=config.chroma_dir,
            collection_name=config.collection_name,
        )

    def ask(self, *, question: str, config: RagConfig) -> QueryResult:
        """Retrieve chunks and generate an answer with LangChain.

        Parameters
        ----------
        question : str
            User question.
        config : RagConfig
            Retrieval and model settings.

        Returns
        -------
        QueryResult
            Answer and citations.

        Raises
        ------
        IndexMissingError
            If the Chroma collection is empty.
        """
        embeddings = HuggingFaceEmbeddings(model_name=config.embed_model_name)
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        collection = client.get_or_create_collection(name=config.collection_name)
        if int(collection.count()) == 0:
            raise IndexMissingError(
                f"Chroma collection '{config.collection_name}' at {config.chroma_dir} is empty. "
                "Run `poe ingest-papers --strategy langchain` first.",
            )
        store = Chroma(
            persist_directory=str(config.chroma_dir),
            embedding_function=embeddings,
            collection_name=config.collection_name,
        )
        retriever = store.as_retriever(
            search_kwargs={"k": config.similarity_top_k * 3},
        )
        retrieved = retriever.invoke(question)
        kept = _select_documents(
            documents=retrieved,
            keep=config.similarity_top_k,
            question=question,
        )
        context = _format_context(documents=kept)
        llm = ChatOpenAI(
            model=config.llm_model_name,
            api_key=require_openai_api_key(),
        )
        prompt = _QA_SYSTEM.format(context=context) + f"\nQuestion: {question}\nAnswer: "
        response = llm.invoke(prompt)
        answer = str(getattr(response, "content", None) or response).strip()
        nodes = [
            SimpleNamespace(
                node=SimpleNamespace(text=doc.page_content, metadata=dict(doc.metadata)),
                score=None,
            )
            for doc in kept
        ]
        citations = citations_from_nodes(nodes=nodes)
        return QueryResult(
            answer=answer,
            citations=citations,
            citations_markdown=format_citations(citations=citations),
        )

    def is_ready(self, *, config: RagConfig) -> bool:
        """Return True when the LangChain Chroma collection is non-empty.

        Parameters
        ----------
        config : RagConfig
            Index configuration.

        Returns
        -------
        bool
            True when at least one chunk is stored.
        """
        try:
            config.ensure_dirs()
            client = chromadb.PersistentClient(path=str(config.chroma_dir))
            collection = client.get_or_create_collection(name=config.collection_name)
            return int(collection.count()) > 0
        except Exception:  # noqa: BLE001 — missing store is "not ready"
            return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({RagStrategy.LANGCHAIN.value})"


def _select_documents(
    *,
    documents: list[Any],
    keep: int,
    question: str,
) -> list[Any]:
    """Keep prose chunks; for author questions drop thanks and prefer early pages."""
    selected: list[Any] = []
    for document in documents:
        text = str(getattr(document, "page_content", "") or "")
        if not is_prose_text(text=text):
            continue
        selected.append(document)
    if is_author_question(question=question):
        without_noise = [
            document
            for document in selected
            if not is_acknowledgement_text(
                text=str(getattr(document, "page_content", "") or ""),
            )
            and not is_proceedings_boilerplate_text(
                text=str(getattr(document, "page_content", "") or ""),
            )
        ]
        if without_noise:
            selected = without_noise
        selected = sorted(selected, key=_page_sort_key)
    return selected[:keep]


def _page_sort_key(document: Any) -> int:
    """Sort key: earlier pages first; missing page sorts last."""
    metadata = dict(getattr(document, "metadata", {}) or {})
    page = page_from_mapping(metadata=metadata)
    return page if page is not None else 10_000


def _format_context(*, documents: list[Any]) -> str:
    """Join chunks with filename/page labels so the LLM can prefer title pages."""
    parts: list[str] = []
    for document in documents:
        metadata = dict(getattr(document, "metadata", {}) or {})
        name = str(metadata.get("file_name", "unknown"))
        page = page_from_mapping(metadata=metadata)
        header = f"[{name}, p.{page}]" if page is not None else f"[{name}]"
        text = str(getattr(document, "page_content", "") or "")
        parts.append(f"{header}\n{text}")
    return "\n\n".join(parts)


def _prose_documents(*, documents: list[Any], keep: int) -> list[Any]:
    """Keep retrieved LangChain documents that look like paper prose."""
    return _select_documents(documents=documents, keep=keep, question="")
