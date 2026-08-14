"""Dispatch ingest/query to the selected orchestration backend."""

from __future__ import annotations

from rag.core.backends.protocol import RagBackend
from rag.core.strategy import RagStrategy


def get_backend(*, strategy: RagStrategy) -> RagBackend:
    """Return the backend implementation for ``strategy``.

    Parameters
    ----------
    strategy : RagStrategy
        Orchestration library.

    Returns
    -------
    RagBackend
        Concrete backend (imported lazily).

    Raises
    ------
    ValueError
        If ``strategy`` has no backend.
    """
    if strategy is RagStrategy.LLAMAINDEX:
        from rag.core.backends.llamaindex import LlamaIndexBackend

        return LlamaIndexBackend()
    if strategy is RagStrategy.LANGCHAIN:
        from rag.core.backends.langchain import LangChainBackend

        return LangChainBackend()
    raise ValueError(f"Unsupported RAG strategy: {strategy}")
