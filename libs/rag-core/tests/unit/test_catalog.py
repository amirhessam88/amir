"""Unit tests for the paper catalog and corpus query routing."""

import json
from pathlib import Path
from types import SimpleNamespace

from assertpy import assert_that

from rag.core.catalog import (
    CATALOG_FILE_NAME,
    TITLE_SNIPPET_CHARS,
    PaperCatalog,
    PaperCatalogEntry,
    QueryScope,
    catalog_from_documents,
    catalog_path,
    classify_query_scope,
    load_paper_catalog,
    title_from_text,
    write_paper_catalog,
)
from rag.core.config import RagConfig


def test_classify_query_scope__corpus_cues() -> None:
    assert_that(
        classify_query_scope(question="What is the common topic among all papers?"),
    ).is_equal_to(QueryScope.CORPUS)
    assert_that(
        classify_query_scope(question="What is a driver node?"),
    ).is_equal_to(QueryScope.PAPER)


def test_title_from_text__truncates() -> None:
    short = "XGBoost for PFAS"
    assert_that(title_from_text(text=f"  {short}  ")).is_equal_to(short)
    long = "word " * (TITLE_SNIPPET_CHARS)
    clipped = title_from_text(text=long)
    assert_that(len(clipped)).is_less_than_or_equal_to(TITLE_SNIPPET_CHARS)
    assert_that(clipped).ends_with("…")


def test_catalog_from_documents__first_page_wins(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    docs = [
        SimpleNamespace(
            text="Title of the work about graphs.",
            metadata={"file_name": str(pdf), "page": 1},
        ),
        SimpleNamespace(
            text="Later page should be ignored.",
            metadata={"file_name": "paper.pdf", "page": 2},
        ),
        SimpleNamespace(text="no meta", metadata="bad"),
        SimpleNamespace(text="no name", metadata={"file_name": ""}),
        SimpleNamespace(text="other", metadata={"file_name": "other.pdf"}),
    ]
    catalog = catalog_from_documents(pdf_paths=[pdf, tmp_path / "orphan.pdf"], documents=docs)
    assert_that(catalog.papers).is_length(2)
    assert_that(catalog.papers[0].file_name).is_equal_to("paper.pdf")
    assert_that(catalog.papers[0].title).contains("Title of the work")
    assert_that(catalog.papers[1].file_name).is_equal_to("orphan.pdf")
    assert_that(catalog.papers[1].title).is_equal_to("")


def test_catalog_markdown_and_json_roundtrip(tmp_path: Path) -> None:
    empty = PaperCatalog(papers=())
    assert_that(empty.to_markdown()).is_equal_to("")
    catalog = PaperCatalog(
        papers=(
            PaperCatalogEntry(file_name="a.pdf", title="Alpha"),
            PaperCatalogEntry(file_name="b.pdf", title=""),
        ),
    )
    markdown = catalog.to_markdown()
    assert_that(markdown).contains("**a.pdf** — Alpha")
    assert_that(markdown).contains("**b.pdf**")
    parsed = PaperCatalog.from_json(catalog.to_json())
    assert_that(parsed).is_equal_to(catalog)
    path = write_paper_catalog(catalog=catalog, chroma_dir=tmp_path)
    assert_that(path.name).is_equal_to(CATALOG_FILE_NAME)
    loaded = load_paper_catalog(
        config=RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path),
    )
    assert_that(loaded).is_equal_to(catalog)


def test_catalog_from_json__skips_bad_rows() -> None:
    raw = json.dumps(
        {
            "papers": [
                {"file_name": "ok.pdf", "title": "Ok"},
                {"file_name": "  ", "title": "skip"},
                "not-a-dict",
            ],
        },
    )
    catalog = PaperCatalog.from_json(raw)
    assert_that(catalog.papers).is_length(1)
    assert_that(catalog.papers[0].file_name).is_equal_to("ok.pdf")
    assert_that(PaperCatalog.from_json("[]").papers).is_equal_to(())
    assert_that(PaperCatalog.from_json("{}").papers).is_equal_to(())
    assert_that(PaperCatalog.from_json('{"papers": {}}').papers).is_equal_to(())


def test_load_paper_catalog__missing_file__filenames_only(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "jmri2020.pdf").write_bytes(b"%PDF")
    catalog = load_paper_catalog(
        config=RagConfig(papers_dir=papers, chroma_dir=tmp_path / "no-chroma"),
    )
    assert_that(catalog.papers).is_length(1)
    assert_that(catalog.papers[0].file_name).is_equal_to("jmri2020.pdf")
    assert_that(catalog.papers[0].title).is_equal_to("")


def test_load_paper_catalog__bad_json__filenames_only(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "xgb-pfas-2022.pdf").write_bytes(b"%PDF")
    chroma = tmp_path / "chroma"
    chroma.mkdir()
    (chroma / CATALOG_FILE_NAME).write_text("{not json", encoding="utf-8")
    catalog = load_paper_catalog(
        config=RagConfig(papers_dir=papers, chroma_dir=chroma),
    )
    assert_that(catalog.papers).is_length(1)
    assert_that(catalog.papers[0].file_name).is_equal_to("xgb-pfas-2022.pdf")
    assert_that(catalog_path(chroma_dir=chroma).name).is_equal_to(CATALOG_FILE_NAME)
