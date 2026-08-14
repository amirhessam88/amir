"""Chroma persistence helpers for the papers collection."""

from __future__ import annotations

from typing import Any

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.core.embeddings import BaseEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from rag.core.config import RagConfig


class IndexMissingError(FileNotFoundError):
    """Raised when the Chroma collection has no documents yet."""


def open_chroma_collection(*, config: RagConfig) -> Any:
    """Open (or create) the persistent Chroma collection.

    Parameters
    ----------
    config : RagConfig
        Paths and collection name.

    Returns
    -------
    chromadb.Collection
        Open collection handle.
    """
    config.ensure_dirs()
    client = chromadb.PersistentClient(path=str(config.chroma_dir))
    return client.get_or_create_collection(name=config.collection_name)


def load_vector_index(
    *,
    config: RagConfig,
    embed_model: BaseEmbedding,
    require_nonempty: bool = True,
) -> VectorStoreIndex:
    """Load a ``VectorStoreIndex`` backed by the persistent Chroma store.

    Parameters
    ----------
    config : RagConfig
        Index configuration.
    embed_model : BaseEmbedding
        Embedding model used at query time (must match ingest).
    require_nonempty : bool
        When True, raise if the collection has zero documents.

    Returns
    -------
    VectorStoreIndex
        LlamaIndex vector index over Chroma.

    Raises
    ------
    IndexMissingError
        If ``require_nonempty`` and the collection is empty.
    """
    collection = open_chroma_collection(config=config)
    count = int(collection.count())
    if require_nonempty and count == 0:
        raise IndexMissingError(
            f"Chroma collection '{config.collection_name}' at {config.chroma_dir} is empty. "
            "Run `poe ingest-papers` first.",
        )
    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model,
    )
