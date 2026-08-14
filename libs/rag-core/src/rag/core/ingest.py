"""PDF ingest pipeline: load → chunk → embed → Chroma."""

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
from pypdf import PdfReader

from rag.core.catalog import catalog_from_documents, write_paper_catalog
from rag.core.citations import FileMetadataKey, PageMetadataKey
from rag.core.config import RagConfig
from rag.core.text_quality import is_prose_text


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


def list_pdf_paths(*, papers_dir: Path) -> list[Path]:
    """List PDF files under ``papers_dir`` (non-recursive).

    Parameters
    ----------
    papers_dir : Path
        Directory containing PDFs.

    Returns
    -------
    list of Path
        Sorted PDF paths.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist or contains no PDFs.
    """
    if not papers_dir.is_dir():
        raise FileNotFoundError(f"Papers directory not found: {papers_dir}")
    paths = sorted(papers_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"No PDF files found in {papers_dir}")
    return paths


def load_pdf_documents(*, pdf_paths: Sequence[Path]) -> list[Document]:
    """Extract per-page text from PDFs with pypdf.

    LlamaIndex ``SimpleDirectoryReader`` has no PDF reader registered in this
    stack, so it would decode raw PDF bytes as UTF-8 and index binary garbage.
    Pages that fail ``is_prose_text`` (figures, dedications, glyph salad) are
    skipped.

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
    documents: list[Document] = []
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for index, page in enumerate(reader.pages):
            raw = page.extract_text() or ""
            if not is_prose_text(text=raw):
                continue
            page_number = index + 1
            documents.append(
                Document(
                    text=raw,
                    metadata={
                        FileMetadataKey.FILE_NAME.value: pdf_path.name,
                        FileMetadataKey.FILE_PATH.value: str(pdf_path),
                        PageMetadataKey.PAGE_LABEL.value: str(page_number),
                        PageMetadataKey.PAGE.value: page_number,
                    },
                ),
            )
    if not documents:
        raise FileNotFoundError(
            "No extractable text found in the PDF corpus. "
            "Check that the files are text PDFs, not image-only scans.",
        )
    return documents


def _reset_collection(*, config: RagConfig) -> Any:
    """Delete and recreate the Chroma collection for a clean rebuild."""
    config.ensure_dirs()
    client = chromadb.PersistentClient(path=str(config.chroma_dir))
    with contextlib.suppress(Exception):
        client.delete_collection(name=config.collection_name)
    return client.get_or_create_collection(name=config.collection_name)


def ingest_papers(
    *,
    config: RagConfig,
    embed_model: BaseEmbedding | None = None,
    rebuild: bool = True,
) -> IngestResult:
    """Ingest PDFs from ``config.papers_dir`` into persistent Chroma.

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
