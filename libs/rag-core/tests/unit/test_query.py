"""Unit tests for query helpers (mocked LLM / engine)."""

from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core import query as query_module
from rag.core.catalog import PaperCatalog, PaperCatalogEntry
from rag.core.citations import Citation
from rag.core.config import OPENAI_API_KEY_ENV, RagConfig
from rag.core.query import (
    ProseNodePostprocessor,
    ask,
    build_llm,
    build_query_engine,
    require_openai_api_key,
)


def test_require_openai_api_key__missing__raises(monkeypatch) -> None:
    monkeypatch.delenv(OPENAI_API_KEY_ENV, raising=False)
    monkeypatch.setattr("rag.core.query.load_repo_dotenv", lambda: None)
    try:
        require_openai_api_key()
        raise AssertionError("expected OSError")
    except OSError as exc:
        assert_that(str(exc)).contains(OPENAI_API_KEY_ENV)


def test_require_openai_api_key__present__returns(monkeypatch) -> None:
    monkeypatch.setenv(OPENAI_API_KEY_ENV, " sk-test ")
    monkeypatch.setattr("rag.core.query.load_repo_dotenv", lambda: None)
    assert_that(require_openai_api_key()).is_equal_to("sk-test")


class _FakeResponse:
    def __init__(self) -> None:
        node = SimpleNamespace(
            text="Context for the question",
            metadata={"file_name": "paper.pdf", "page_label": "1"},
        )
        self.source_nodes = [SimpleNamespace(node=node, score=0.88)]

    def __str__(self) -> str:
        return "Because the paper says so."


class _FakeEngine:
    def query(self, question: str) -> Any:
        _ = question
        return _FakeResponse()


def test_ask__with_injected_engine__returns_citations(tmp_path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    result = ask(
        question="What is the main result?",
        config=config,
        query_engine=_FakeEngine(),
    )
    assert_that(result.answer).contains("paper says so")
    assert_that(result.citations).is_length(1)
    assert_that(result.citations[0]).is_instance_of(Citation)
    assert_that(result.citations[0].file_name).is_equal_to("paper.pdf")
    assert_that(result.citations_markdown).contains("paper.pdf")


def test_ask__corpus_question__uses_catalog_not_engine(tmp_path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    catalog = PaperCatalog(
        papers=(
            PaperCatalogEntry(file_name="xgb-pfas-2022.pdf", title="XGBoost PFAS"),
            PaperCatalogEntry(file_name="jmri2020.pdf", title="MRI deep learning"),
        ),
    )
    llm = MagicMock()
    llm.complete.return_value = SimpleNamespace(
        text="Applied machine learning across environmental and medical imaging work.",
    )

    class _BoomEngine:
        def query(self, question: str) -> Any:
            _ = question
            raise AssertionError("vector RAG must not run for corpus questions")

    result = ask(
        question="What is the common topic among all papers?",
        config=config,
        query_engine=_BoomEngine(),
        catalog=catalog,
        llm=llm,
    )
    llm.complete.assert_called_once()
    assert_that(result.answer).contains("Applied machine learning")
    assert_that(result.citations).is_length(2)
    assert_that(result.citations_markdown).contains("xgb-pfas-2022.pdf")


def test_ask__corpus_question__loads_catalog_and_llm(tmp_path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    catalog = PaperCatalog(
        papers=(PaperCatalogEntry(file_name="a.pdf", title="Alpha"),),
    )
    llm = MagicMock()
    llm.complete.return_value = SimpleNamespace(text="")
    with (
        patch("rag.core.query.load_paper_catalog", return_value=catalog),
        patch("rag.core.query.build_llm", return_value=llm) as build,
    ):
        result = ask(
            question="common theme across all papers",
            config=config,
        )
    build.assert_called_once()
    assert_that(result.answer).is_not_empty()


def test_ask__corpus_empty_catalog__raises(tmp_path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    llm = MagicMock()
    try:
        ask(
            question="body of work across all papers",
            config=config,
            catalog=PaperCatalog(papers=()),
            llm=llm,
        )
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert_that(str(exc)).contains("catalog")
    llm.complete.assert_not_called()


def test_build_llm__uses_config_model(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("rag.core.query.load_repo_dotenv", lambda: None)
    config = RagConfig(
        papers_dir=tmp_path,
        chroma_dir=tmp_path / "chroma",
        llm_model_name="gpt-4o-mini",
    )
    with patch("rag.core.query.OpenAI") as openai_cls:
        openai_cls.return_value = MagicMock(name="llm")
        llm = build_llm(config=config, api_key="sk-x")
        openai_cls.assert_called_once_with(model="gpt-4o-mini", api_key="sk-x")
        assert_that(llm).is_equal_to(openai_cls.return_value)


def test_build_query_engine__wires_index(tmp_path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma", similarity_top_k=4)
    fake_index = MagicMock()
    fake_engine = MagicMock(name="engine")
    fake_index.as_query_engine.return_value = fake_engine
    embed = MagicMock()
    llm = MagicMock()

    with patch("rag.core.query.Settings"):
        engine = build_query_engine(
            config=config,
            embed_model=embed,
            llm=llm,
            index=fake_index,
        )
    assert_that(engine).is_equal_to(fake_engine)
    fake_index.as_query_engine.assert_called_once()
    kwargs = fake_index.as_query_engine.call_args.kwargs
    assert_that(kwargs["similarity_top_k"]).is_equal_to(12)
    assert_that(kwargs["llm"]).is_equal_to(llm)
    assert_that(kwargs["text_qa_template"]).is_equal_to(
        query_module.PAPERS_TEXT_QA_TEMPLATE,
    )
    assert_that(kwargs["refine_template"]).is_equal_to(
        query_module.PAPERS_REFINE_TEMPLATE,
    )
    processors = kwargs["node_postprocessors"]
    assert_that(processors).is_length(1)
    assert_that(processors[0].keep).is_equal_to(4)


_PROSE_CHUNK = (
    "NewsAnalyticalToolkit is an online natural language processing platform "
    "to analyze news. The system extracts topics and sentiment from articles "
    "published by national outlets during special elections."
)

_JUNK_CHUNK = (
    '1.0 - 0.8 - 0.4 - ó 0.6 SadnessDisgustAngerFearJoy 6h o*("< cyeoe5 '
    "ayo By ArticleBy Site ThPKPmbaWlly 530 abcO+ FlveThirlyEight"
)


def test_prose_postprocessor__filters_junk_and_respects_keep() -> None:
    junk = SimpleNamespace(get_content=lambda: _JUNK_CHUNK)
    first = SimpleNamespace(get_content=lambda: _PROSE_CHUNK)
    second = SimpleNamespace(get_content=lambda: _PROSE_CHUNK)
    processor = ProseNodePostprocessor(keep=1)
    kept = processor._postprocess_nodes(
        nodes=[junk, first, second],
        query_bundle=object(),
    )
    assert_that(kept).is_equal_to([first])


def test_prose_postprocessor__empty_and_under_keep() -> None:
    processor = ProseNodePostprocessor(keep=3)
    assert_that(processor._postprocess_nodes(nodes=[])).is_equal_to([])
    first = SimpleNamespace(get_content=lambda: _PROSE_CHUNK)
    kept = processor._postprocess_nodes(nodes=[first])
    assert_that(kept).is_equal_to([first])


def test_scored_node_text__node_text_attribute() -> None:
    item = SimpleNamespace(node=SimpleNamespace(text="hello from node"))
    assert_that(query_module._scored_node_text(item=item)).is_equal_to(
        "hello from node",
    )


def test_scored_node_text__node_get_content() -> None:
    item = SimpleNamespace(
        node=SimpleNamespace(text=None, get_content=lambda: "via getter"),
    )
    assert_that(query_module._scored_node_text(item=item)).is_equal_to(
        "via getter",
    )


def test_scored_node_text__empty() -> None:
    item = SimpleNamespace(node=SimpleNamespace())
    assert_that(query_module._scored_node_text(item=item)).is_equal_to("")
