"""Streamlit query chat over the local papers Chroma index."""

from __future__ import annotations

import os
import sys
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

import streamlit as st

from rag.core import (
    IndexMissingError,
    RagConfig,
    ask,
    build_query_engine,
)
from rag.core.config import OPENAI_API_KEY_ENV, OPENAI_MODEL_ENV, load_repo_dotenv


class ChatRole(StrEnum):
    """Roles stored in the Streamlit chat transcript."""

    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageKey(StrEnum):
    """Keys on each message dict in ``st.session_state``."""

    ROLE = "role"
    CONTENT = "content"
    CITATIONS = "citations"


MESSAGES_STATE_KEY: Final = "messages"
_STREAMLIT_FILE_WATCHER: Final = "none"


def _secrets_api_key() -> str | None:
    """Read OpenAI key from Streamlit secrets when available."""
    try:
        value = st.secrets.get(OPENAI_API_KEY_ENV)  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001 — secrets.toml may be absent locally
        return None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@lru_cache(maxsize=1)
def _cached_config() -> RagConfig:
    return RagConfig.from_env()


def _ensure_api_key() -> None:
    load_repo_dotenv()
    if os.environ.get(OPENAI_API_KEY_ENV, "").strip():
        return
    from_secrets = _secrets_api_key()
    if from_secrets:
        os.environ[OPENAI_API_KEY_ENV] = from_secrets


@st.cache_resource(show_spinner="Loading query engine…")
def _get_query_engine(*, top_k: int) -> tuple[Any, RagConfig]:
    _ensure_api_key()
    config = _cached_config()
    tuned = RagConfig(
        papers_dir=config.papers_dir,
        chroma_dir=config.chroma_dir,
        collection_name=config.collection_name,
        embed_model_name=config.embed_model_name,
        llm_model_name=os.environ.get(OPENAI_MODEL_ENV, config.llm_model_name),
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        similarity_top_k=top_k,
    )
    return build_query_engine(config=tuned), tuned


def main() -> None:
    """Render the Papers RAG chat UI."""
    load_repo_dotenv()
    st.set_page_config(
        page_title="Papers RAG",
        page_icon="🧠",
        layout="wide",
    )
    st.title("🧠 Papers RAG")
    st.caption(
        "Ask questions grounded in the research PDFs under `assets/pdf/papers`. "
        "Factoid questions retrieve chunks; questions about *all papers* "
        "(common theme, whole corpus) use the full paper catalog. "
        "Embeddings + Chroma are local; chat uses your OpenAI API key.",
    )

    with st.sidebar:
        st.header("⚙️ Settings")
        config = _cached_config()
        st.write(f"**LLM:** `{os.environ.get(OPENAI_MODEL_ENV, config.llm_model_name)}`")
        st.write(f"**Embed:** `{config.embed_model_name}`")
        st.write(f"**Chroma:** `{config.chroma_dir}`")
        top_k = st.slider(
            "Similarity top-k", min_value=1, max_value=12, value=config.similarity_top_k
        )
        if st.button("🗑️ Clear chat"):
            st.session_state[MESSAGES_STATE_KEY] = []
            st.rerun()
        st.markdown(
            "Run ingest first if the index is empty:\n\n`poe ingest-papers`",
        )

    if MESSAGES_STATE_KEY not in st.session_state:
        st.session_state[MESSAGES_STATE_KEY] = []

    for message in st.session_state[MESSAGES_STATE_KEY]:
        with st.chat_message(message[ChatMessageKey.ROLE]):
            st.markdown(message[ChatMessageKey.CONTENT])
            if message.get(ChatMessageKey.CITATIONS):
                with st.expander("📚 Sources"):
                    st.markdown(message[ChatMessageKey.CITATIONS])

    prompt = st.chat_input("Ask about the papers…")
    if not prompt:
        return

    st.session_state[MESSAGES_STATE_KEY].append(
        {
            ChatMessageKey.ROLE: ChatRole.USER,
            ChatMessageKey.CONTENT: prompt,
        },
    )
    with st.chat_message(ChatRole.USER):
        st.markdown(prompt)

    with st.chat_message(ChatRole.ASSISTANT):
        try:
            engine, tuned = _get_query_engine(top_k=top_k)
            with st.spinner("Retrieving + generating…"):
                result = ask(question=prompt, config=tuned, query_engine=engine)
        except IndexMissingError as exc:
            st.error(str(exc))
            return
        except OSError as exc:
            st.error(str(exc))
            return
        except Exception as exc:  # noqa: BLE001 — UI boundary
            st.error(f"Query failed: {exc}")
            return

        st.markdown(result.answer)
        if result.citations_markdown:
            with st.expander("📚 Sources", expanded=True):
                st.markdown(result.citations_markdown)

    st.session_state[MESSAGES_STATE_KEY].append(
        {
            ChatMessageKey.ROLE: ChatRole.ASSISTANT,
            ChatMessageKey.CONTENT: result.answer,
            ChatMessageKey.CITATIONS: result.citations_markdown,
        },
    )


def run() -> None:
    """Launch Streamlit for the papers chat (console script ``papers-rag``).

    Extra CLI args after ``papers-rag`` are forwarded to ``streamlit run``.
    """
    from streamlit.web.cli import main as streamlit_main

    extra = sys.argv[1:]
    sys.argv = [
        "streamlit",
        "run",
        str(Path(__file__).resolve()),
        "--server.fileWatcherType",
        _STREAMLIT_FILE_WATCHER,
        *extra,
    ]
    streamlit_main()


if __name__ == "__main__":
    main()
