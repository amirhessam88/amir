"""Query / chat engine over the papers Chroma index."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Final

from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.prompts import PromptTemplate
from llama_index.core.query_engine import BaseQueryEngine
from llama_index.llms.openai import OpenAI
from pydantic import Field

from rag.core.catalog import (
    PaperCatalog,
    QueryScope,
    classify_query_scope,
    load_paper_catalog,
)
from rag.core.citations import Citation, citations_from_nodes, format_citations
from rag.core.config import OPENAI_API_KEY_ENV, RagConfig, load_repo_dotenv
from rag.core.index import load_vector_index
from rag.core.ingest import build_embed_model
from rag.core.text_quality import is_prose_text

RETRIEVAL_OVERFETCH: Final = 3

PAPERS_TEXT_QA_TEMPLATE = PromptTemplate(
    "Context from research papers is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Answer the question using only this context. Be concise and direct "
    "(a few sentences unless the question needs more). These excerpts are a "
    "retrieved subset — not the full library. Do not say 'all papers' or "
    "'both papers' unless you list every filename you used. If the question "
    "is about the whole corpus, say this context is too narrow.\n"
    "Question: {query_str}\n"
    "Answer: ",
)

PAPERS_REFINE_TEMPLATE = PromptTemplate(
    "The original question is: {query_str}\n"
    "We have an existing answer: {existing_answer}\n"
    "We have new context:\n"
    "------------\n"
    "{context_msg}\n"
    "------------\n"
    "Update the answer only if the new context helps. Stay concise. "
    "If the new context is not useful, keep the original answer.\n"
    "Answer: ",
)


class ProseNodePostprocessor(BaseNodePostprocessor):
    """Keep retrieved chunks that look like readable paper prose.

    Attributes
    ----------
    keep : int
        Maximum number of prose nodes to retain after filtering.
    """

    keep: int = Field(default=5)

    def _postprocess_nodes(
        self,
        nodes: list[Any],
        query_bundle: Any | None = None,
    ) -> list[Any]:
        """Filter ``nodes`` to prose text, then cap at ``keep``.

        Parameters
        ----------
        nodes : list
            Retrieved ``NodeWithScore`` objects.
        query_bundle : object or None
            Unused; required by LlamaIndex.

        Returns
        -------
        list
            Prose nodes in retrieval order, length at most ``keep``.
        """
        _ = query_bundle
        selected: list[Any] = []
        for item in nodes:
            if not is_prose_text(text=_scored_node_text(item=item)):
                continue
            selected.append(item)
            if len(selected) >= self.keep:
                break
        return selected


def _scored_node_text(*, item: Any) -> str:
    """Read text from a ``NodeWithScore`` or a bare node-like object.

    Parameters
    ----------
    item : object
        LlamaIndex scored node or a test stand-in.

    Returns
    -------
    str
        Node text, or an empty string when none is present.
    """
    get_content = getattr(item, "get_content", None)
    if callable(get_content):
        return str(get_content())
    node = getattr(item, "node", item)
    raw = getattr(node, "text", None)
    if raw:
        return str(raw)
    getter = getattr(node, "get_content", None)
    if callable(getter):
        return str(getter())
    return ""


@dataclass(frozen=True, kw_only=True)
class QueryResult:
    """Answer plus grounding citations.

    Attributes
    ----------
    answer : str
        Model response text.
    citations : list of Citation
        Retrieved sources.
    citations_markdown : str
        Pre-formatted markdown for UIs.
    """

    answer: str
    citations: list[Citation]
    citations_markdown: str


def require_openai_api_key() -> str:
    """Load ``.env`` if present and return ``OPENAI_API_KEY``.

    Returns
    -------
    str
        API key value.

    Raises
    ------
    EnvironmentError
        If the key is missing or empty.
    """
    load_repo_dotenv()
    key = os.environ.get(OPENAI_API_KEY_ENV, "").strip()
    if not key:
        raise OSError(
            f"{OPENAI_API_KEY_ENV} is not set. Copy .env.example to .env and add your key.",
        )
    return key


def build_llm(*, config: RagConfig, api_key: str | None = None) -> OpenAI:
    """Construct the OpenAI chat LLM.

    Parameters
    ----------
    config : RagConfig
        Provides ``llm_model_name``.
    api_key : str or None
        Explicit key; otherwise read from the environment.

    Returns
    -------
    OpenAI
        LlamaIndex OpenAI LLM wrapper.
    """
    key = api_key if api_key is not None else require_openai_api_key()
    return OpenAI(model=config.llm_model_name, api_key=key)


def build_query_engine(
    *,
    config: RagConfig,
    embed_model: BaseEmbedding | None = None,
    llm: Any | None = None,
    index: VectorStoreIndex | None = None,
) -> BaseQueryEngine:
    """Build a retrieval-augmented query engine.

    Parameters
    ----------
    config : RagConfig
        Retrieval and model settings.
    embed_model : BaseEmbedding or None
        Defaults to the HuggingFace model from config.
    llm : Any or None
        Defaults to OpenAI from config + env key.
    index : VectorStoreIndex or None
        Defaults to loading the persistent Chroma index.

    Returns
    -------
    BaseQueryEngine
        Configured LlamaIndex query engine.
    """
    model = embed_model or build_embed_model(config=config)
    chat_llm = llm or build_llm(config=config)
    Settings.embed_model = model
    Settings.llm = chat_llm
    vector_index = index or load_vector_index(config=config, embed_model=model)
    return vector_index.as_query_engine(
        similarity_top_k=config.similarity_top_k * RETRIEVAL_OVERFETCH,
        llm=chat_llm,
        text_qa_template=PAPERS_TEXT_QA_TEMPLATE,
        refine_template=PAPERS_REFINE_TEMPLATE,
        node_postprocessors=[
            ProseNodePostprocessor(keep=config.similarity_top_k),
        ],
    )


CORPUS_SYNTHESIS_PROMPT: Final = (
    "You are summarizing a researcher's full PDF library.\n"
    "The catalog below is the COMPLETE set of papers ({paper_count} files), "
    "not a retrieval sample.\n"
    "---------------------\n"
    "{catalog_markdown}\n"
    "---------------------\n"
    "If the files span multiple application domains (medical imaging, "
    "networks, environment, finance, news, engineering, …) but share "
    "supervised learning, deep learning, graph ML, or similar methods, "
    "the unifying theme is applied machine learning. State that umbrella "
    "first, then name several distinct domains from the filenames/titles. "
    "Do not treat one paper as the whole corpus.\n"
    "Question: {query_str}\n"
    "Answer: "
)


def ask(
    *,
    question: str,
    config: RagConfig,
    query_engine: BaseQueryEngine | None = None,
    catalog: PaperCatalog | None = None,
    llm: Any | None = None,
) -> QueryResult:
    """Ask a question against the papers index or the full corpus catalog.

    Corpus-level questions (for example "common topic among all papers")
    skip vector retrieval and synthesize from the paper catalog.

    Parameters
    ----------
    question : str
        User question.
    config : RagConfig
        Used when constructing a default engine or loading the catalog.
    query_engine : BaseQueryEngine or None
        Injected engine (tests / Streamlit cache).
    catalog : PaperCatalog or None
        Injected catalog; otherwise loaded from disk or ``papers_dir``.
    llm : Any or None
        Injected chat LLM for corpus synthesis.

    Returns
    -------
    QueryResult
        Answer and citations.
    """
    if classify_query_scope(question=question) is QueryScope.CORPUS:
        papers = catalog if catalog is not None else load_paper_catalog(config=config)
        chat_llm = llm if llm is not None else build_llm(config=config)
        return _ask_corpus(question=question, catalog=papers, llm=chat_llm)
    engine = query_engine or build_query_engine(config=config)
    response = engine.query(question)
    source_nodes = list(getattr(response, "source_nodes", []) or [])
    citations = citations_from_nodes(nodes=source_nodes)
    answer = str(response).strip()
    return QueryResult(
        answer=answer,
        citations=citations,
        citations_markdown=format_citations(citations=citations),
    )


def _ask_corpus(
    *,
    question: str,
    catalog: PaperCatalog,
    llm: Any,
) -> QueryResult:
    """Synthesize an answer from the full paper catalog.

    Parameters
    ----------
    question : str
        Corpus-level question.
    catalog : PaperCatalog
        Complete paper list.
    llm : Any
        LlamaIndex-style LLM with ``complete``.

    Returns
    -------
    QueryResult
        Answer plus catalog citations.

    Raises
    ------
    FileNotFoundError
        If the catalog has no papers.
    """
    if not catalog.papers:
        raise FileNotFoundError(
            "Paper catalog is empty. Run `poe ingest-papers` to build it.",
        )
    prompt = CORPUS_SYNTHESIS_PROMPT.format(
        paper_count=len(catalog.papers),
        catalog_markdown=catalog.to_markdown(),
        query_str=question,
    )
    response = llm.complete(prompt)
    answer = str(getattr(response, "text", None) or response).strip()
    citations = _citations_from_catalog(catalog=catalog)
    return QueryResult(
        answer=answer,
        citations=citations,
        citations_markdown=format_citations(citations=citations),
    )


def _citations_from_catalog(*, catalog: PaperCatalog) -> list[Citation]:
    """Turn catalog entries into citations (filename + title snippet).

    Parameters
    ----------
    catalog : PaperCatalog
        Full paper list.

    Returns
    -------
    list of Citation
        One citation per catalog entry.
    """
    return [
        Citation(
            file_name=entry.file_name,
            page=None,
            score=None,
            snippet=entry.title,
        )
        for entry in catalog.papers
    ]
