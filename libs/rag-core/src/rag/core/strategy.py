"""RAG orchestration strategies (one persist dir per strategy)."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Final

RAG_STRATEGY_ENV: Final = "RAG_STRATEGY"
INDEXES_DIR_NAME: Final = "indexes"
INGEST_ALL: Final = "all"


class RagStrategy(StrEnum):
    """In-process orchestration library used to ingest and query the PDF corpus."""

    LLAMAINDEX = "llamaindex"
    LANGCHAIN = "langchain"

    @classmethod
    def ingestible(cls) -> tuple[RagStrategy, ...]:
        """Return strategies that write a local index via ``papers-ingest``.

        Returns
        -------
        tuple of RagStrategy
            Every in-process backend (LlamaIndex and LangChain).
        """
        return tuple(cls)


def index_dir_for(*, repo_root: Path, strategy: RagStrategy) -> Path:
    """Return the default persist directory for a strategy.

    Parameters
    ----------
    repo_root : Path
        Monorepo root.
    strategy : RagStrategy
        Orchestration backend.

    Returns
    -------
    Path
        ``{repo_root}/.data/indexes/{strategy}``.
    """
    return (repo_root / ".data" / INDEXES_DIR_NAME / strategy.value).resolve()
