"""Tests for the LangChain backend (mocked embeddings / Chroma / LLM)."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core.backends.langchain.backend import (
    LangChainBackend,
    _format_context,
    _prose_documents,
    _select_documents,
)
from rag.core.config import RagConfig
from rag.core.index import IndexMissingError
from rag.core.ingest import IngestResult
from rag.core.loaders import PageDocument

_PROSE = (
    "Driver nodes control complex networks in systems biology. "
    "These vertices determine whether a directed network can be driven "
    "from any initial state to any desired final state."
)
_THANKS = (
    "The authors would like to thank Tessa Daniels for the careful revision "
    "of the manuscript. Additional colleagues provided comments on earlier "
    "drafts of this SPIE proceedings paper on spatio-temporal analysis."
)
_AUTHORS = (
    "Brian M. Cullum, Douglas Kiehl, Eric S. McLamore wrote this SPIE paper "
    "on regulators of microbial communities in soil and water systems with "
    "supervised learning methods applied to sensor data."
)
_AUTHORS_LATE = (
    "Corresponding authors appear in the footer of later pages in this "
    "proceedings volume along with affiliations for the imaging group and "
    "the university laboratory that hosted the experiments."
)
_EDITORS = (
    "Smart Biomedical and Physiological Sensor Technology XIV, edited by "
    "Brian M. Cullum, Douglas Kiehl, Eric S. McLamore, Proc. of SPIE Vol. "
    "10216, 1021605 with a CCC code for this proceedings paper on sensors."
)


def test_langchain_ingest__writes_collection(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF-1.4")
    config = RagConfig(
        papers_dir=papers,
        chroma_dir=tmp_path / "chroma",
        collection_name="papers",
    )
    page = PageDocument(text=_PROSE, metadata={"file_name": "a.pdf"})
    fake_collection = MagicMock()
    fake_collection.count.return_value = 4
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection

    with (
        patch(
            "rag.core.backends.langchain.backend.load_pdf_pages",
            return_value=[page],
        ),
        patch("rag.core.backends.langchain.backend.write_paper_catalog"),
        patch("rag.core.backends.langchain.backend._reset_collection"),
        patch("rag.core.backends.langchain.backend.HuggingFaceEmbeddings"),
        patch("rag.core.backends.langchain.backend.RecursiveCharacterTextSplitter") as splitter_cls,
        patch("rag.core.backends.langchain.backend.Chroma") as chroma_cls,
        patch(
            "rag.core.backends.langchain.backend.chromadb.PersistentClient",
            return_value=fake_client,
        ),
    ):
        splitter = MagicMock()
        splitter.split_documents.return_value = [MagicMock()]
        splitter_cls.return_value = splitter
        result = LangChainBackend().ingest(config=config, rebuild=True)

    assert_that(result).is_instance_of(IngestResult)
    assert_that(result.documents).is_equal_to(1)
    assert_that(result.nodes).is_equal_to(4)
    chroma_cls.from_documents.assert_called_once()


def test_langchain_ingest__append__skips_reset(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF-1.4")
    config = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "chroma")
    page = PageDocument(text=_PROSE, metadata={"file_name": "a.pdf"})
    fake_collection = MagicMock()
    fake_collection.count.return_value = 1
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection

    with (
        patch(
            "rag.core.backends.langchain.backend.load_pdf_pages",
            return_value=[page],
        ),
        patch("rag.core.backends.langchain.backend.write_paper_catalog"),
        patch("rag.core.backends.langchain.backend._reset_collection") as reset,
        patch("rag.core.backends.langchain.backend.HuggingFaceEmbeddings"),
        patch("rag.core.backends.langchain.backend.RecursiveCharacterTextSplitter") as splitter_cls,
        patch("rag.core.backends.langchain.backend.Chroma"),
        patch(
            "rag.core.backends.langchain.backend.chromadb.PersistentClient",
            return_value=fake_client,
        ),
    ):
        splitter_cls.return_value.split_documents.return_value = [MagicMock()]
        LangChainBackend().ingest(config=config, rebuild=False, embed_model=object())
    reset.assert_not_called()


def test_langchain_ask__empty_index__raises(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_collection = MagicMock()
    fake_collection.count.return_value = 0
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection
    with (
        patch("rag.core.backends.langchain.backend.HuggingFaceEmbeddings"),
        patch(
            "rag.core.backends.langchain.backend.chromadb.PersistentClient",
            return_value=fake_client,
        ),
    ):
        try:
            LangChainBackend().ask(question="What is a driver node?", config=config)
            raise AssertionError("expected IndexMissingError")
        except IndexMissingError as exc:
            assert_that(str(exc)).contains("langchain")


def test_langchain_ask__returns_citations(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_collection = MagicMock()
    fake_collection.count.return_value = 2
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection
    doc = SimpleNamespace(
        page_content=_PROSE,
        metadata={"file_name": "paper.pdf", "page": 1},
    )
    store = MagicMock()
    store.as_retriever.return_value.invoke.return_value = [doc]
    llm = MagicMock()
    llm.invoke.return_value = SimpleNamespace(content="Because the paper says so.")

    with (
        patch("rag.core.backends.langchain.backend.HuggingFaceEmbeddings"),
        patch(
            "rag.core.backends.langchain.backend.chromadb.PersistentClient",
            return_value=fake_client,
        ),
        patch("rag.core.backends.langchain.backend.Chroma", return_value=store),
        patch("rag.core.backends.langchain.backend.ChatOpenAI", return_value=llm),
        patch(
            "rag.core.backends.langchain.backend.require_openai_api_key",
            return_value="sk-test",
        ),
    ):
        result = LangChainBackend().ask(question="What is a driver node?", config=config)

    assert_that(result.answer).contains("paper says so")
    assert_that(result.citations).is_length(1)
    assert_that(result.citations[0].file_name).is_equal_to("paper.pdf")


def test_langchain_is_ready(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_collection = MagicMock()
    fake_collection.count.return_value = 2
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection
    with patch(
        "rag.core.backends.langchain.backend.chromadb.PersistentClient",
        return_value=fake_client,
    ):
        assert_that(LangChainBackend().is_ready(config=config)).is_true()
    fake_collection.count.side_effect = RuntimeError("nope")
    with patch(
        "rag.core.backends.langchain.backend.chromadb.PersistentClient",
        return_value=fake_client,
    ):
        assert_that(LangChainBackend().is_ready(config=config)).is_false()


def test_select_documents__author_question__drops_thanks_and_prefers_early_page() -> None:
    thanks = SimpleNamespace(
        page_content=_THANKS,
        metadata={"file_name": "spie.pdf", "page": 11},
    )
    authors = SimpleNamespace(
        page_content=_AUTHORS,
        metadata={"file_name": "spie.pdf", "page": 2},
    )
    late = SimpleNamespace(
        page_content=_AUTHORS_LATE,
        metadata={"file_name": "spie.pdf", "page": 9},
    )
    editors = SimpleNamespace(
        page_content=_EDITORS,
        metadata={"file_name": "spie.pdf", "page": 2},
    )
    missing = SimpleNamespace(
        page_content=_PROSE,
        metadata={"file_name": "other.pdf"},
    )
    none_meta = SimpleNamespace(page_content=_PROSE, metadata=None)
    kept = _select_documents(
        documents=[thanks, late, editors, missing, authors, none_meta],
        keep=5,
        question="who is the main author",
    )
    assert_that(kept).is_equal_to([authors, late, missing, none_meta])


def test_select_documents__author_question__keeps_thanks_when_only_hit() -> None:
    thanks = SimpleNamespace(
        page_content=_THANKS,
        metadata={"file_name": "spie.pdf", "page": 11},
    )
    kept = _select_documents(
        documents=[thanks],
        keep=1,
        question="who is the main author",
    )
    assert_that(kept).is_equal_to([thanks])


def test_select_documents__non_author_keeps_thanks() -> None:
    thanks = SimpleNamespace(
        page_content=_THANKS,
        metadata={"file_name": "spie.pdf", "page": 11},
    )
    kept = _select_documents(documents=[thanks], keep=1, question="What was revised?")
    assert_that(kept).is_equal_to([thanks])


def test_format_context__labels_file_and_page() -> None:
    doc = SimpleNamespace(
        page_content=_PROSE,
        metadata={"file_name": "paper.pdf", "page": 1},
    )
    formatted = _format_context(documents=[doc])
    assert_that(formatted).contains("[paper.pdf, p.1]")
    assert_that(formatted).contains("Driver nodes")
    unlabeled = SimpleNamespace(page_content=_PROSE, metadata={})
    assert_that(_format_context(documents=[unlabeled])).contains("[unknown]")
    none_meta = SimpleNamespace(page_content=_PROSE, metadata=None)
    assert_that(_format_context(documents=[none_meta])).contains("[unknown]")
    junk = SimpleNamespace(page_content="1.0 - 0.8 SadnessDisgustAngerFearJoy xxx")
    first = SimpleNamespace(page_content=_PROSE)
    second = SimpleNamespace(page_content=_PROSE)
    kept = _prose_documents(documents=[junk, first, second], keep=1)
    assert_that(kept).is_equal_to([first])
    assert_that(_prose_documents(documents=[], keep=3)).is_equal_to([])


def test_langchain_backend_repr() -> None:
    assert_that(repr(LangChainBackend())).contains("langchain")
