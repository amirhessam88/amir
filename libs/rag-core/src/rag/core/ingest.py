"""PDF ingest pipeline: load → chunk → embed → Chroma (LlamaIndex path)."""

from __future__ import annotations

import contextlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from rag.core.catalog import catalog_from_documents, write_paper_catalog
from rag.core.config import RagConfig
from rag.core.loaders import list_pdf_paths, load_pdf_pages
from rag.core.strategy import RagStrategy


@dataclass(frozen=True, kw_only=True)
class IngestResult:
    """Summary of an ingest run.

    Attributes
    ----------
    documents : int
        Number of page-level documents written (PDFs with extractable text).
    nodes : int
        Number of chunks written to Chroma.
    chroma_dir : Path
        Persistence directory used.
    collection_name : str
        Chroma collection name.
    """

    documents: int
    nodes: int
    chroma_dir: Path
    collection_name: str


def build_embed_model(*, config: RagConfig) -> HuggingFaceEmbedding:
    """Construct the local HuggingFace embedding model.

    Parameters
    ----------
    config : RagConfig
        Provides ``embed_model_name``.

    Returns
    -------
    HuggingFaceEmbedding
        LlamaIndex embedding wrapper.
    """
    return HuggingFaceEmbedding(model_name=config.embed_model_name)


def load_pdf_documents(*, pdf_paths: Sequence[Path]) -> list[Document]:
    """Extract per-page LlamaIndex documents from PDFs.

    Parameters
    ----------
    pdf_paths : sequence of Path
        PDF files to load.

    Returns
    -------
    list of Document
        One LlamaIndex document per extractable page.

    Raises
    ------
    FileNotFoundError
        If no page yields extractable text.
    """
    return [
        Document(text=page.text, metadata=dict(page.metadata))
        for page in load_pdf_pages(pdf_paths=pdf_paths)
    ]


def _reset_collection(*, config: RagConfig) -> Any:
    """Delete and recreate the Chroma collection for a clean rebuild."""
    config.ensure_dirs()
    client = chromadb.PersistentClient(path=str(config.chroma_dir))
    with contextlib.suppress(Exception):
        client.delete_collection(name=config.collection_name)
    return client.get_or_create_collection(name=config.collection_name)


def ingest_llamaindex(
    *,
    config: RagConfig,
    embed_model: BaseEmbedding | None = None,
    rebuild: bool = True,
) -> IngestResult:
    """Ingest PDFs with LlamaIndex into persistent Chroma.

    Parameters
    ----------
    config : RagConfig
        Paths, chunking, and model settings.
    embed_model : BaseEmbedding or None
        Optional pre-built embedder (tests can inject a stub).
    rebuild : bool
        When True, delete the existing collection before writing.

    Returns
    -------
    IngestResult
        Counts and paths for the run.
    """
    pdf_paths = list_pdf_paths(papers_dir=config.papers_dir)
    model = embed_model or build_embed_model(config=config)
    Settings.embed_model = model
    Settings.node_parser = SentenceSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )

    if rebuild:
        collection = _reset_collection(config=config)
    else:
        config.ensure_dirs()
        client = chromadb.PersistentClient(path=str(config.chroma_dir))
        collection = client.get_or_create_collection(name=config.collection_name)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    documents = load_pdf_documents(pdf_paths=pdf_paths)
    write_paper_catalog(
        catalog=catalog_from_documents(pdf_paths=pdf_paths, documents=documents),
        chroma_dir=config.chroma_dir,
    )
    index = VectorStoreIndex.from_documents(
        documents=documents,
        storage_context=storage_context,
        embed_model=model,
        show_progress=True,
    )
    _ = index
    node_count = int(collection.count())
    return IngestResult(
        documents=len(documents),
        nodes=node_count,
        chroma_dir=config.chroma_dir,
        collection_name=config.collection_name,
    )


def ingest_papers(
    *,
    config: RagConfig,
    embed_model: BaseEmbedding | None = None,
    rebuild: bool = True,
) -> IngestResult:
    """Ingest PDFs using ``config.strategy``.

    Parameters
    ----------
    config : RagConfig
        Paths, chunking, model settings, and orchestration strategy.
    embed_model : BaseEmbedding or None
        Optional LlamaIndex embedder (ignored by other backends).
    rebuild : bool
        When True, delete the existing collection before writing.

    Returns
    -------
    IngestResult
        Counts and paths for the run.
    """
    if config.strategy is RagStrategy.LLAMAINDEX:
        return ingest_llamaindex(
            config=config,
            embed_model=embed_model,
            rebuild=rebuild,
        )
    from rag.core.backends.registry import get_backend

    return get_backend(strategy=config.strategy).ingest(
        config=config,
        rebuild=rebuild,
        embed_model=embed_model,
    )
