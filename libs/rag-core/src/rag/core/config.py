"""Configuration for the papers RAG pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

from rag.core.strategy import RAG_STRATEGY_ENV, RagStrategy, index_dir_for

PAPERS_DIR_ENV: Final = "PAPERS_DIR"
CHROMA_DIR_ENV: Final = "CHROMA_DIR"
CHROMA_COLLECTION_ENV: Final = "CHROMA_COLLECTION"
EMBED_MODEL_ENV: Final = "EMBED_MODEL"
OPENAI_API_KEY_ENV: Final = "OPENAI_API_KEY"
OPENAI_MODEL_ENV: Final = "OPENAI_MODEL"
CHUNK_SIZE_ENV: Final = "CHUNK_SIZE"
CHUNK_OVERLAP_ENV: Final = "CHUNK_OVERLAP"
SIMILARITY_TOP_K_ENV: Final = "SIMILARITY_TOP_K"

DEFAULT_COLLECTION_NAME: Final = "papers"
DEFAULT_EMBED_MODEL: Final = "BAAI/bge-small-en-v1.5"
DEFAULT_LLM_MODEL: Final = "gpt-4o-mini"
DEFAULT_CHUNK_SIZE: Final = 1024
DEFAULT_CHUNK_OVERLAP: Final = 128
DEFAULT_SIMILARITY_TOP_K: Final = 5


def find_repo_root(*, start: Path | None = None) -> Path:
    """Walk parents until the monorepo root (contains ``libs/rag-core``) is found.

    Parameters
    ----------
    start : Path or None
        Directory to start from. Defaults to this file's location.

    Returns
    -------
    Path
        Absolute path to the monorepo root.

    Raises
    ------
    FileNotFoundError
        If no ancestor contains ``libs/rag-core``.
    """
    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "libs" / "rag-core").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not locate monorepo root (expected libs/rag-core). "
        "Pass RagConfig paths explicitly or run from inside the repo.",
    )


def load_repo_dotenv() -> None:
    """Load ``.env`` from cwd and the monorepo root.

    Existing process environment wins (``override=False``). Streamlit sets
    cwd to the script directory, so a repo-root ``.env`` is missed by a
    bare ``load_dotenv()``.
    """
    load_dotenv()
    try:
        load_dotenv(find_repo_root() / ".env")
    except FileNotFoundError:
        return


@dataclass(frozen=True, kw_only=True)
class RagConfig:
    """Runtime settings for ingest + query.

    Attributes
    ----------
    papers_dir : Path
        Directory of PDF papers to ingest.
    chroma_dir : Path
        Persistent Chroma directory (created if missing).
    collection_name : str
        Chroma collection name.
    embed_model_name : str
        HuggingFace embedding model id (local).
    llm_model_name : str
        OpenAI chat model id.
    chunk_size : int
        SentenceSplitter chunk size.
    chunk_overlap : int
        SentenceSplitter overlap.
    similarity_top_k : int
        Retrieval top-k for the query engine.
    strategy : RagStrategy
        In-process orchestration backend (LlamaIndex or LangChain).
    """

    papers_dir: Path
    chroma_dir: Path
    collection_name: str = DEFAULT_COLLECTION_NAME
    embed_model_name: str = DEFAULT_EMBED_MODEL
    llm_model_name: str = DEFAULT_LLM_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    similarity_top_k: int = DEFAULT_SIMILARITY_TOP_K
    strategy: RagStrategy = RagStrategy.LLAMAINDEX

    @classmethod
    def from_env(
        cls,
        *,
        repo_root: Path | None = None,
        strategy: RagStrategy | None = None,
    ) -> RagConfig:
        """Build config from environment variables with repo-relative defaults.

        Parameters
        ----------
        repo_root : Path or None
            Monorepo root. Discovered automatically when omitted.
        strategy : RagStrategy or None
            Orchestration backend. Defaults to ``RAG_STRATEGY`` or LlamaIndex.

        Returns
        -------
        RagConfig
            Resolved configuration.
        """
        root = repo_root or find_repo_root()
        chosen = strategy or RagStrategy(
            os.environ.get(RAG_STRATEGY_ENV, RagStrategy.LLAMAINDEX.value),
        )
        papers = Path(
            os.environ.get(PAPERS_DIR_ENV, root / "assets" / "pdf" / "papers"),
        )
        chroma_raw = os.environ.get(CHROMA_DIR_ENV)
        chroma = Path(chroma_raw) if chroma_raw else index_dir_for(repo_root=root, strategy=chosen)
        if not papers.is_absolute():
            papers = (root / papers).resolve()
        if not chroma.is_absolute():
            chroma = (root / chroma).resolve()
        return cls(
            papers_dir=papers,
            chroma_dir=chroma,
            collection_name=os.environ.get(
                CHROMA_COLLECTION_ENV,
                DEFAULT_COLLECTION_NAME,
            ),
            embed_model_name=os.environ.get(EMBED_MODEL_ENV, DEFAULT_EMBED_MODEL),
            llm_model_name=os.environ.get(OPENAI_MODEL_ENV, DEFAULT_LLM_MODEL),
            chunk_size=int(
                os.environ.get(CHUNK_SIZE_ENV, str(DEFAULT_CHUNK_SIZE)),
            ),
            chunk_overlap=int(
                os.environ.get(CHUNK_OVERLAP_ENV, str(DEFAULT_CHUNK_OVERLAP)),
            ),
            similarity_top_k=int(
                os.environ.get(SIMILARITY_TOP_K_ENV, str(DEFAULT_SIMILARITY_TOP_K)),
            ),
            strategy=chosen,
        )

    def ensure_dirs(self) -> None:
        """Create the Chroma persistence directory if needed."""
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
