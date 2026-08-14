"""Tests for strategy helpers and backend registry."""

from pathlib import Path

from assertpy import assert_that

from rag.core.backends import IngestNotSupportedError, get_backend
from rag.core.backends.langchain import LangChainBackend
from rag.core.backends.llamaindex import LlamaIndexBackend
from rag.core.config import RagConfig
from rag.core.ingest import IngestResult
from rag.core.query import QueryResult
from rag.core.strategy import RagStrategy, index_dir_for


def test_ingest_not_supported_error_type() -> None:
    try:
        raise IngestNotSupportedError("studio")
    except IngestNotSupportedError as exc:
        assert_that(str(exc)).is_equal_to("studio")


def test_index_dir_for__scopes_by_strategy(tmp_path: Path) -> None:
    path = index_dir_for(repo_root=tmp_path, strategy=RagStrategy.LANGCHAIN)
    assert_that(path).is_equal_to((tmp_path / ".data" / "indexes" / "langchain").resolve())


def test_rag_strategy_ingestible__is_all_members() -> None:
    assert_that(RagStrategy.ingestible()).is_equal_to(
        (RagStrategy.LLAMAINDEX, RagStrategy.LANGCHAIN),
    )


def test_get_backend__llamaindex() -> None:
    assert_that(get_backend(strategy=RagStrategy.LLAMAINDEX)).is_instance_of(
        LlamaIndexBackend,
    )


def test_get_backend__langchain() -> None:
    assert_that(get_backend(strategy=RagStrategy.LANGCHAIN)).is_instance_of(
        LangChainBackend,
    )


def test_get_backend__unknown__raises() -> None:
    try:
        get_backend(strategy="nope")  # type: ignore[arg-type]
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert_that(str(exc)).contains("Unsupported")


def test_llamaindex_backend_repr() -> None:
    assert_that(repr(LlamaIndexBackend())).contains("llamaindex")


def test_llamaindex_backend_ingest_and_ask(tmp_path: Path, monkeypatch) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    ingest_result = IngestResult(
        documents=1,
        nodes=2,
        chroma_dir=config.chroma_dir,
        collection_name="papers",
    )
    query_result = QueryResult(answer="ok", citations=[], citations_markdown="")
    monkeypatch.setattr(
        "rag.core.ingest.ingest_llamaindex",
        lambda **kwargs: ingest_result,
    )
    monkeypatch.setattr(
        "rag.core.query.ask_llamaindex",
        lambda **kwargs: query_result,
    )
    backend = LlamaIndexBackend()
    assert_that(backend.ingest(config=config, rebuild=True)).is_equal_to(ingest_result)
    assert_that(backend.ask(question="q", config=config)).is_equal_to(query_result)


def test_llamaindex_backend_is_ready(tmp_path: Path, monkeypatch) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    collection = type("C", (), {"count": staticmethod(lambda: 3)})()
    monkeypatch.setattr(
        "rag.core.index.open_chroma_collection",
        lambda **kwargs: collection,
    )
    assert_that(LlamaIndexBackend().is_ready(config=config)).is_true()
    monkeypatch.setattr(
        "rag.core.index.open_chroma_collection",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    assert_that(LlamaIndexBackend().is_ready(config=config)).is_false()
    empty = type("C", (), {"count": staticmethod(lambda: 0)})()
    monkeypatch.setattr(
        "rag.core.index.open_chroma_collection",
        lambda **kwargs: empty,
    )
    assert_that(LlamaIndexBackend().is_ready(config=config)).is_false()
