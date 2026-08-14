"""Unit tests for ingest helpers (no model download)."""

from pathlib import Path

from assertpy import assert_that

from rag.core.citations import FileMetadataKey, PageMetadataKey
from rag.core.ingest import load_pdf_documents
from rag.core.loaders import list_pdf_paths


def test_list_pdf_paths__sorted__returns_pdfs(tmp_path: Path) -> None:
    (tmp_path / "b.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "a.pdf").write_bytes(b"%PDF-1.4")
    (tmp_path / "notes.txt").write_text("skip", encoding="utf-8")
    paths = list_pdf_paths(papers_dir=tmp_path)
    assert_that([path.name for path in paths]).is_equal_to(["a.pdf", "b.pdf"])


def test_list_pdf_paths__missing_dir__raises(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    try:
        list_pdf_paths(papers_dir=missing)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert_that(str(exc)).contains("not found")


def test_list_pdf_paths__empty_dir__raises(tmp_path: Path) -> None:
    try:
        list_pdf_paths(papers_dir=tmp_path)
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert_that(str(exc)).contains("No PDF")


class _FakePage:
    """PdfReader page stand-in with a fixed extract_text result."""

    def __init__(self, text: str | None) -> None:
        self._text = text

    def extract_text(self) -> str | None:
        return self._text


def test_load_pdf_documents__pages__sets_metadata(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    class _FakeReader:
        def __init__(self, path: Path) -> None:
            _ = path
            self.pages = [
                _FakePage(
                    "Driver nodes control complex networks in systems biology. "
                    "These vertices determine whether a directed network can be "
                    "driven from any initial state to any desired final state."
                ),
                _FakePage(""),
                _FakePage("x"),
                _FakePage(None),
            ]

    monkeypatch.setattr("rag.core.loaders.PdfReader", _FakeReader)
    docs = load_pdf_documents(pdf_paths=[pdf])
    assert_that(docs).is_length(1)
    assert_that(docs[0].text).contains("Driver nodes")
    assert_that(docs[0].metadata[FileMetadataKey.FILE_NAME.value]).is_equal_to(
        "paper.pdf",
    )
    assert_that(docs[0].metadata[PageMetadataKey.PAGE.value]).is_equal_to(1)
    assert_that(docs[0].metadata[PageMetadataKey.PAGE_LABEL.value]).is_equal_to("1")


def test_load_pdf_documents__empty_corpus__raises(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    class _FakeReader:
        def __init__(self, path: Path) -> None:
            _ = path
            self.pages = [_FakePage("   too short   ")]

    monkeypatch.setattr("rag.core.loaders.PdfReader", _FakeReader)
    try:
        load_pdf_documents(pdf_paths=[pdf])
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        assert_that(str(exc)).contains("extractable")


def test_load_pdf_documents__figure_dump__skipped(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4")
    prose = (
        "Driver nodes control complex networks in systems biology. "
        "These vertices determine whether a directed network can be "
        "driven from any initial state to any desired final state."
    )
    junk = (
        "1.0 - 0.8 - 0.4 - ó 0.6 - 02 - 0.0 SadnessDisgustAngerFearJoy "
        '6h o*("< cyeoe5 ayo By ArticleBy Site .. . . óz- + OP co p '
        "ThPKPmbaWlly 530 abcO+ FlveThirlyEight cbsO ABC cnnO+ ces"
    )

    class _FakeReader:
        def __init__(self, path: Path) -> None:
            _ = path
            self.pages = [_FakePage(prose), _FakePage(junk)]

    monkeypatch.setattr("rag.core.loaders.PdfReader", _FakeReader)
    docs = load_pdf_documents(pdf_paths=[pdf])
    assert_that(docs).is_length(1)
    assert_that(docs[0].text).contains("Driver nodes")
