"""Streamlit query chat over the local papers Chroma index."""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Any, Final

import streamlit as st

from rag.core import (
    IndexMissingError,
    RagConfig,
    RagStrategy,
    ask,
    build_query_engine,
)
from rag.core.backends.registry import get_backend
from rag.core.config import (
    CHROMA_DIR_ENV,
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL_ENV,
    find_repo_root,
    load_repo_dotenv,
)
from rag.core.strategy import index_dir_for


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
STRATEGY_STATE_KEY: Final = "rag_strategy"
_STREAMLIT_FILE_WATCHER: Final = "none"
_LOGO_RELATIVE: Final = Path("assets") / "img" / "logo_color_clear.png"
_FALLBACK_PAGE_ICON: Final = "🧠"
_SOURCES_EXPANDER_LABEL: Final = "📚 Sources"
_STRATEGY_LABELS: Final = {
    RagStrategy.LLAMAINDEX: "LlamaIndex",
    RagStrategy.LANGCHAIN: "LangChain",
}


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


def _strategy_label(value: str) -> str:
    """Return the sidebar label for a strategy value."""
    return _STRATEGY_LABELS[RagStrategy(value)]


def _page_icon() -> str:
    """Return the repo logo path, or an emoji when assets are missing."""
    try:
        logo = find_repo_root() / _LOGO_RELATIVE
    except FileNotFoundError:
        return _FALLBACK_PAGE_ICON
    if logo.is_file():
        return str(logo)
    return _FALLBACK_PAGE_ICON


def _ensure_api_key() -> None:
    load_repo_dotenv()
    if os.environ.get(OPENAI_API_KEY_ENV, "").strip():
        return
    from_secrets = _secrets_api_key()
    if from_secrets:
        os.environ[OPENAI_API_KEY_ENV] = from_secrets


def _config_for_strategy(*, strategy: RagStrategy, top_k: int) -> RagConfig:
    """Build a tuned config for the sidebar strategy and top-k."""
    base = _cached_config()
    if os.environ.get(CHROMA_DIR_ENV):
        chroma = base.chroma_dir
    else:
        chroma = index_dir_for(repo_root=find_repo_root(), strategy=strategy)
    return replace(
        base,
        strategy=strategy,
        chroma_dir=chroma,
        similarity_top_k=top_k,
        llm_model_name=os.environ.get(OPENAI_MODEL_ENV, base.llm_model_name),
    )


@st.cache_resource(show_spinner="Loading query engine…")
def _get_query_engine(
    *,
    top_k: int,
    strategy: str = RagStrategy.LLAMAINDEX.value,
) -> tuple[Any, RagConfig]:
    _ensure_api_key()
    tuned = _config_for_strategy(strategy=RagStrategy(strategy), top_k=top_k)
    return build_query_engine(config=tuned), tuned


def main() -> None:
    """Render the Papers RAG chat UI."""
    load_repo_dotenv()
    st.set_page_config(
        page_title="Papers RAG",
        page_icon=_page_icon(),
        layout="wide",
    )
    st.title("🧠 Papers RAG")
    st.caption(
        "Ask questions grounded in the research PDFs under `assets/pdf/papers`. "
        "Pick a strategy to load that pattern's local index (same PDFs, isolated DBs). "
        "Factoid questions retrieve chunks; questions about *all papers* or "
        "*who wrote these* use the full paper catalog. Chat uses your OpenAI API key.",
    )

    with st.sidebar:
        st.header("⚙️ Settings")
        config = _cached_config()
        strategy_value = st.selectbox(
            "Strategy",
            options=[item.value for item in RagStrategy],
            format_func=_strategy_label,
            help="Each strategy has its own persist dir under .data/indexes/.",
        )
        strategy = RagStrategy(str(strategy_value))
        if (
            STRATEGY_STATE_KEY in st.session_state
            and st.session_state[STRATEGY_STATE_KEY] != strategy.value
        ):
            st.session_state[MESSAGES_STATE_KEY] = []
        st.session_state[STRATEGY_STATE_KEY] = strategy.value
        top_k = st.slider(
            "Similarity top-k", min_value=1, max_value=12, value=config.similarity_top_k
        )
        tuned = _config_for_strategy(strategy=strategy, top_k=top_k)
        ready = get_backend(strategy=strategy).is_ready(config=tuned)
        st.write(f"**LLM:** `{tuned.llm_model_name}`")
        st.write(f"**Embed:** `{tuned.embed_model_name}`")
        st.write(f"**Chroma:** `{tuned.chroma_dir}`")
        st.write(f"**Index:** {'ready' if ready else 'empty — ingest first'}")
        if st.button("🗑️ Clear chat"):
            st.session_state[MESSAGES_STATE_KEY] = []
            st.rerun()
        st.markdown(
            "Ingest per strategy:\n\n"
            "`poe ingest-papers --strategy llamaindex`\n\n"
            "`poe ingest-papers --strategy langchain`",
        )

    if MESSAGES_STATE_KEY not in st.session_state:
        st.session_state[MESSAGES_STATE_KEY] = []

    for message in st.session_state[MESSAGES_STATE_KEY]:
        with st.chat_message(message[ChatMessageKey.ROLE]):
            st.markdown(message[ChatMessageKey.CONTENT])
            if message.get(ChatMessageKey.CITATIONS):
                with st.expander(_SOURCES_EXPANDER_LABEL, expanded=False):
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
            if strategy is RagStrategy.LLAMAINDEX:
                engine, query_config = _get_query_engine(
                    top_k=top_k,
                    strategy=strategy.value,
                )
                with st.spinner("Retrieving + generating…"):
                    result = ask(
                        question=prompt,
                        config=query_config,
                        query_engine=engine,
                    )
            else:
                _ensure_api_key()
                with st.spinner("Retrieving + generating…"):
                    result = ask(question=prompt, config=tuned)
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
            with st.expander(_SOURCES_EXPANDER_LABEL, expanded=False):
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
