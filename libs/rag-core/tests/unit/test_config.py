"""Unit tests for RagConfig and repo root discovery."""

import os
from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that

from rag.core.config import (
    CHROMA_DIR_ENV,
    DEFAULT_EMBED_MODEL,
    DEFAULT_LLM_MODEL,
    OPENAI_API_KEY_ENV,
    OPENAI_MODEL_ENV,
    PAPERS_DIR_ENV,
    SIMILARITY_TOP_K_ENV,
    RagConfig,
    find_repo_root,
    load_repo_dotenv,
)


def test_find_repo_root__from_lib_src__returns_workspace() -> None:
    root = find_repo_root()
    assert_that((root / "libs" / "rag-core").is_dir()).is_true()
    assert_that((root / "assets" / "pdf" / "papers").is_dir()).is_true()


def test_find_repo_root__missing__raises(tmp_path: Path) -> None:
    try:
        find_repo_root(start=tmp_path)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert_that(str(exc)).contains("libs/rag-core")


def test_rag_config_from_env__defaults__resolve_under_repo(monkeypatch) -> None:
    monkeypatch.delenv(PAPERS_DIR_ENV, raising=False)
    monkeypatch.delenv(CHROMA_DIR_ENV, raising=False)
    monkeypatch.delenv(OPENAI_MODEL_ENV, raising=False)
    root = find_repo_root()
    config = RagConfig.from_env(repo_root=root)
    assert_that(config.papers_dir).is_equal_to((root / "assets" / "pdf" / "papers").resolve())
    assert_that(config.chroma_dir).is_equal_to((root / ".data" / "chroma" / "papers").resolve())
    assert_that(config.llm_model_name).is_equal_to(DEFAULT_LLM_MODEL)
    assert_that(config.embed_model_name).is_equal_to(DEFAULT_EMBED_MODEL)


def test_rag_config_from_env__overrides__honor_env(monkeypatch, tmp_path: Path) -> None:
    papers = tmp_path / "pdfs"
    chroma = tmp_path / "chroma"
    papers.mkdir()
    monkeypatch.setenv(PAPERS_DIR_ENV, str(papers))
    monkeypatch.setenv(CHROMA_DIR_ENV, str(chroma))
    monkeypatch.setenv(OPENAI_MODEL_ENV, "gpt-4o")
    monkeypatch.setenv(SIMILARITY_TOP_K_ENV, "3")
    config = RagConfig.from_env(repo_root=tmp_path)
    assert_that(config.papers_dir).is_equal_to(papers.resolve())
    assert_that(config.chroma_dir).is_equal_to(chroma.resolve())
    assert_that(config.llm_model_name).is_equal_to("gpt-4o")
    assert_that(config.similarity_top_k).is_equal_to(3)


def test_rag_config_from_env__relative_paths__resolve_under_repo(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(PAPERS_DIR_ENV, "relative/papers")
    monkeypatch.setenv(CHROMA_DIR_ENV, "relative/chroma")
    config = RagConfig.from_env(repo_root=tmp_path)
    assert_that(config.papers_dir).is_equal_to((tmp_path / "relative" / "papers").resolve())
    assert_that(config.chroma_dir).is_equal_to((tmp_path / "relative" / "chroma").resolve())


def test_rag_config_from_env__discovers_repo_root(monkeypatch) -> None:
    monkeypatch.delenv(PAPERS_DIR_ENV, raising=False)
    monkeypatch.delenv(CHROMA_DIR_ENV, raising=False)
    config = RagConfig.from_env()
    root = find_repo_root()
    assert_that(config.papers_dir).is_equal_to((root / "assets" / "pdf" / "papers").resolve())


def test_ensure_dirs__creates_chroma_parent(tmp_path: Path) -> None:
    chroma = tmp_path / "nested" / "chroma"
    config = RagConfig(papers_dir=tmp_path, chroma_dir=chroma)
    config.ensure_dirs()
    assert_that(chroma.is_dir()).is_true()


def test_load_repo_dotenv__reads_repo_root_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"{OPENAI_API_KEY_ENV}=from-file\n")
    with patch("rag.core.config.find_repo_root", return_value=tmp_path):
        load_repo_dotenv()
    assert_that(os.environ.get(OPENAI_API_KEY_ENV)).is_equal_to("from-file")
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)


def test_load_repo_dotenv__loads_when_cwd_is_not_repo(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)
    repo = tmp_path / "repo"
    script_dir = tmp_path / "script"
    repo.mkdir()
    script_dir.mkdir()
    (repo / ".env").write_text(f"{OPENAI_API_KEY_ENV}=from-repo\n")
    monkeypatch.chdir(script_dir)
    with patch("rag.core.config.find_repo_root", return_value=repo):
        load_repo_dotenv()
    assert_that(os.environ.get(OPENAI_API_KEY_ENV)).is_equal_to("from-repo")
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)


def test_load_repo_dotenv__does_not_override_process_env(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv(OPENAI_API_KEY_ENV, "from-shell")
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"{OPENAI_API_KEY_ENV}=from-file\n")
    with patch("rag.core.config.find_repo_root", return_value=tmp_path):
        load_repo_dotenv()
    assert_that(os.environ.get(OPENAI_API_KEY_ENV)).is_equal_to("from-shell")


def test_load_repo_dotenv__missing_repo__does_not_raise(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    with patch(
        "rag.core.config.find_repo_root",
        side_effect=FileNotFoundError("nope"),
    ):
        load_repo_dotenv()
