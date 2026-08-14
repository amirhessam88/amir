"""Unit tests for Streamlit app helpers and chat wiring."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from papers_rag import __version__
from papers_rag import app as app_module
from rag.core import IndexMissingError, QueryResult, RagConfig
from rag.core.config import OPENAI_API_KEY_ENV, OPENAI_MODEL_ENV


def test_version__is_semver_like() -> None:
    assert_that(__version__).matches(r"^\d+\.\d+\.\d+$")


def test_secrets_api_key__exception__returns_none() -> None:
    with patch.object(app_module.st, "secrets") as secrets:
        secrets.get.side_effect = RuntimeError("no secrets")
        assert_that(app_module._secrets_api_key()).is_none()


def test_secrets_api_key__blank__returns_none() -> None:
    with patch.object(app_module.st, "secrets") as secrets:
        secrets.get.return_value = "   "
        assert_that(app_module._secrets_api_key()).is_none()


def test_secrets_api_key__present__returns_stripped() -> None:
    with patch.object(app_module.st, "secrets") as secrets:
        secrets.get.return_value = " sk-test "
        assert_that(app_module._secrets_api_key()).is_equal_to("sk-test")


def test_secrets_api_key__none_value__returns_none() -> None:
    with patch.object(app_module.st, "secrets") as secrets:
        secrets.get.return_value = None
        assert_that(app_module._secrets_api_key()).is_none()


def test_ensure_api_key__env_present__noop(monkeypatch) -> None:
    monkeypatch.setenv(OPENAI_API_KEY_ENV, "from-env")
    with patch.object(app_module, "_secrets_api_key") as secrets_key:
        app_module._ensure_api_key()
        secrets_key.assert_not_called()
    assert_that(app_module.os.environ.get(OPENAI_API_KEY_ENV)).is_equal_to("from-env")


def test_ensure_api_key__from_secrets__sets_env(monkeypatch) -> None:
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)
    with (
        patch.object(app_module, "load_repo_dotenv"),
        patch.object(app_module, "_secrets_api_key", return_value="from-secrets"),
    ):
        app_module._ensure_api_key()
    assert_that(app_module.os.environ.get(OPENAI_API_KEY_ENV)).is_equal_to("from-secrets")


def test_ensure_api_key__missing_everywhere__leaves_unset(monkeypatch) -> None:
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)
    with (
        patch.object(app_module, "load_repo_dotenv"),
        patch.object(app_module, "_secrets_api_key", return_value=None),
    ):
        app_module._ensure_api_key()
    assert_that(app_module.os.environ.get(OPENAI_API_KEY_ENV, "")).is_equal_to("")


def test_cached_config__returns_rag_config(tmp_path: Path, monkeypatch) -> None:
    app_module._cached_config.cache_clear()
    monkeypatch.setenv("PAPERS_DIR", str(tmp_path / "papers"))
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    config = app_module._cached_config()
    assert_that(config).is_instance_of(RagConfig)
    app_module._cached_config.cache_clear()


def test_get_query_engine__builds_tuned_config(tmp_path: Path, monkeypatch) -> None:
    app_module._cached_config.cache_clear()
    monkeypatch.setenv("PAPERS_DIR", str(tmp_path / "papers"))
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv(OPENAI_MODEL_ENV, "gpt-test")
    engine = object()
    get_engine = getattr(
        app_module._get_query_engine,
        "__wrapped__",
        app_module._get_query_engine,
    )
    with (
        patch.object(app_module, "_ensure_api_key"),
        patch.object(app_module, "build_query_engine", return_value=engine) as build,
    ):
        got_engine, tuned = get_engine(top_k=7)
    assert_that(got_engine).is_equal_to(engine)
    assert_that(tuned.similarity_top_k).is_equal_to(7)
    assert_that(tuned.llm_model_name).is_equal_to("gpt-test")
    build.assert_called_once()
    app_module._cached_config.cache_clear()


def _config(tmp_path: Path) -> RagConfig:
    return RagConfig(papers_dir=tmp_path / "papers", chroma_dir=tmp_path / "chroma")


def test_main__no_prompt__returns_early(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt=None)
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
    ):
        app_module.main()
    assert_that(st.session_state[app_module.MESSAGES_STATE_KEY]).is_empty()


def test_main__clear_chat__reruns(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt=None, clear_clicked=True)
    st.session_state[app_module.MESSAGES_STATE_KEY] = [
        {
            app_module.ChatMessageKey.ROLE: app_module.ChatRole.USER,
            app_module.ChatMessageKey.CONTENT: "hi",
        },
    ]
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
    ):
        app_module.main()
    assert_that(st.session_state[app_module.MESSAGES_STATE_KEY]).is_empty()
    st.rerun.assert_called_once()


def test_main__ask_success__appends_assistant(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt="What is a driver node?")
    result = QueryResult(
        answer="A control node.",
        citations=[],
        citations_markdown="1. **a.pdf**",
    )
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
        patch.object(
            app_module,
            "_get_query_engine",
            return_value=(object(), _config(tmp_path)),
        ),
        patch.object(app_module, "ask", return_value=result),
    ):
        app_module.main()
    messages = st.session_state[app_module.MESSAGES_STATE_KEY]
    assert_that(messages).is_length(2)
    assert_that(messages[-1][app_module.ChatMessageKey.CONTENT]).is_equal_to(
        "A control node.",
    )
    assert_that(messages[-1][app_module.ChatMessageKey.CITATIONS]).contains("a.pdf")
    assert_that(messages[-1][app_module.ChatMessageKey.ROLE]).is_equal_to(
        app_module.ChatRole.ASSISTANT,
    )


def test_main__ask_success__without_citations(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt="Hello")
    result = QueryResult(answer="Hi", citations=[], citations_markdown="")
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
        patch.object(
            app_module,
            "_get_query_engine",
            return_value=(object(), _config(tmp_path)),
        ),
        patch.object(app_module, "ask", return_value=result),
    ):
        app_module.main()
    messages = st.session_state[app_module.MESSAGES_STATE_KEY]
    assert_that(messages[-1][app_module.ChatMessageKey.CITATIONS]).is_equal_to("")


def test_main__index_missing__shows_error(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt="Q")
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
        patch.object(
            app_module,
            "_get_query_engine",
            side_effect=IndexMissingError("empty index"),
        ),
    ):
        app_module.main()
    st.error.assert_called_with("empty index")
    assert_that(st.session_state[app_module.MESSAGES_STATE_KEY]).is_length(1)


def test_main__oserror__shows_error(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt="Q")
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
        patch.object(app_module, "_get_query_engine", side_effect=OSError("disk")),
    ):
        app_module.main()
    st.error.assert_called_with("disk")


def test_main__generic_error__shows_error(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt="Q")
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
        patch.object(app_module, "_get_query_engine", side_effect=RuntimeError("boom")),
    ):
        app_module.main()
    st.error.assert_called_with("Query failed: boom")


def test_run__invokes_streamlit_cli(monkeypatch) -> None:
    monkeypatch.setattr(app_module.sys, "argv", ["papers-rag", "--server.port", "9999"])
    with patch("streamlit.web.cli.main") as streamlit_main:
        app_module.run()
    streamlit_main.assert_called_once()
    argv = app_module.sys.argv
    assert_that(argv[0]).is_equal_to("streamlit")
    assert_that(argv[1]).is_equal_to("run")
    assert_that(argv[2]).ends_with("app.py")
    assert_that(argv).contains("--server.fileWatcherType", "none", "--server.port", "9999")


def test_main__history_with_citations__renders_expander(tmp_path: Path) -> None:
    st = _fake_streamlit(prompt=None)
    st.session_state[app_module.MESSAGES_STATE_KEY] = [
        {
            app_module.ChatMessageKey.ROLE: app_module.ChatRole.USER,
            app_module.ChatMessageKey.CONTENT: "prior question",
        },
        {
            app_module.ChatMessageKey.ROLE: app_module.ChatRole.ASSISTANT,
            app_module.ChatMessageKey.CONTENT: "prior",
            app_module.ChatMessageKey.CITATIONS: "1. **x.pdf**",
        },
    ]
    with (
        patch.object(app_module, "st", st),
        patch.object(app_module, "_cached_config", return_value=_config(tmp_path)),
    ):
        app_module.main()
    st.expander.assert_called()


class _SessionState(dict):
    """Minimal Streamlit session_state stand-in (item + attribute access)."""

    def __getattr__(self, key: str) -> object:
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key: str, value: object) -> None:
        self[key] = value


def _fake_streamlit(*, prompt: str | None, clear_clicked: bool = False) -> MagicMock:
    st = MagicMock()
    st.session_state = _SessionState()
    st.chat_input.return_value = prompt
    st.slider.return_value = 5
    st.button.return_value = clear_clicked
    st.sidebar = MagicMock()
    st.sidebar.__enter__ = MagicMock(return_value=st.sidebar)
    st.sidebar.__exit__ = MagicMock(return_value=False)
    chat_cm = MagicMock()
    chat_cm.__enter__ = MagicMock(return_value=chat_cm)
    chat_cm.__exit__ = MagicMock(return_value=False)
    st.chat_message.return_value = chat_cm
    expander_cm = MagicMock()
    expander_cm.__enter__ = MagicMock(return_value=expander_cm)
    expander_cm.__exit__ = MagicMock(return_value=False)
    st.expander.return_value = expander_cm
    spinner_cm = MagicMock()
    spinner_cm.__enter__ = MagicMock(return_value=spinner_cm)
    spinner_cm.__exit__ = MagicMock(return_value=False)
    st.spinner.return_value = spinner_cm
    return st
