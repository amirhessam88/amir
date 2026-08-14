"""Backend protocol for ingest + query over a strategy-scoped index."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from rag.core.config import RagConfig
    from rag.core.ingest import IngestResult
    from rag.core.query import QueryResult


class IngestNotSupportedError(RuntimeError):
    """Raised when a strategy cannot ingest via ``papers-ingest``."""


class RagBackend(Protocol):
    """Ingest and query one local (or remote) RAG strategy."""

    def ingest(
        self,
        *,
        config: RagConfig,
        rebuild: bool = True,
        embed_model: object | None = None,
    ) -> IngestResult:
        """Write the PDF corpus into this strategy's index."""

    def ask(self, *, question: str, config: RagConfig) -> QueryResult:
        """Answer a paper-level question from this strategy's index."""

    def is_ready(self, *, config: RagConfig) -> bool:
        """Return True when the local index can answer questions."""
