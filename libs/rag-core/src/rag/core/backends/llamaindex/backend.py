"""LlamaIndex ingest + query over a strategy-scoped Chroma directory."""

from __future__ import annotations

from rag.core.config import RagConfig
from rag.core.ingest import IngestResult
from rag.core.query import QueryResult
from rag.core.strategy import RagStrategy


class LlamaIndexBackend:
    """LlamaIndex ``VectorStoreIndex`` + Chroma backend."""

    def ingest(
        self,
        *,
        config: RagConfig,
        rebuild: bool = True,
        embed_model: object | None = None,
    ) -> IngestResult:
        """Write PDFs into the LlamaIndex Chroma collection.

        Parameters
        ----------
        config : RagConfig
            Paths, chunking, and model settings.
        rebuild : bool
            When True, delete the existing collection before writing.
        embed_model : object or None
            Optional LlamaIndex embedder (tests inject a stub).

        Returns
        -------
        IngestResult
            Counts and paths for the run.
        """
        from rag.core.ingest import ingest_llamaindex

        return ingest_llamaindex(
            config=config,
            rebuild=rebuild,
            embed_model=embed_model,
        )

    def ask(self, *, question: str, config: RagConfig) -> QueryResult:
        """Answer a paper-level question from the LlamaIndex query engine.

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
        """
        from rag.core.query import ask_llamaindex

        return ask_llamaindex(question=question, config=config)

    def is_ready(self, *, config: RagConfig) -> bool:
        """Return True when the LlamaIndex Chroma collection is non-empty.

        Parameters
        ----------
        config : RagConfig
            Index configuration.

        Returns
        -------
        bool
            True when at least one chunk is stored.
        """
        from rag.core.index import open_chroma_collection

        try:
            collection = open_chroma_collection(config=config)
            return int(collection.count()) > 0
        except Exception:  # noqa: BLE001 — missing dir / collection is "not ready"
            return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({RagStrategy.LLAMAINDEX.value})"
