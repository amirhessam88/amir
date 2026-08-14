"""Pluggable RAG orchestration backends."""

from rag.core.backends.protocol import IngestNotSupportedError, RagBackend
from rag.core.backends.registry import get_backend

__all__ = [
    "IngestNotSupportedError",
    "RagBackend",
    "get_backend",
]
