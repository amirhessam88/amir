"""Shared RAG primitives for the amir monorepo."""

from rag.core.citations import Citation, citations_from_nodes, format_citations
from rag.core.config import RagConfig, find_repo_root
from rag.core.index import IndexMissingError, load_vector_index, open_chroma_collection
from rag.core.ingest import ingest_papers
from rag.core.query import QueryResult, ask, build_query_engine
from rag.core.strategy import RagStrategy

__all__ = [
    "Citation",
    "IndexMissingError",
    "QueryResult",
    "RagConfig",
    "RagStrategy",
    "ask",
    "build_query_engine",
    "citations_from_nodes",
    "find_repo_root",
    "format_citations",
    "ingest_papers",
    "load_vector_index",
    "open_chroma_collection",
]
