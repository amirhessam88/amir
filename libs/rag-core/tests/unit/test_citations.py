"""Unit tests for citation formatting."""

from types import SimpleNamespace

from assertpy import assert_that

from rag.core.citations import (
    UNKNOWN_FILE_NAME,
    Citation,
    citations_from_nodes,
    format_citations,
)


def test_citations_from_nodes__metadata__maps_fields() -> None:
    node = SimpleNamespace(
        text="Driver nodes control complex networks in systems biology.",
        metadata={
            "file_name": "/tmp/papers/driver-nodes.pdf",
            "page_label": "3",
        },
    )
    scored = SimpleNamespace(node=node, score=0.91)
    citations = citations_from_nodes(nodes=[scored])
    assert_that(citations).is_length(1)
    assert_that(citations[0].file_name).is_equal_to("driver-nodes.pdf")
    assert_that(citations[0].page).is_equal_to(3)
    assert_that(citations[0].score).is_equal_to(0.91)
    assert_that(citations[0].snippet).contains("Driver nodes")


def test_citations_from_nodes__zero_based_page__normalizes() -> None:
    node = SimpleNamespace(
        text="hello",
        metadata={"file_path": "x.pdf", "page": 0},
    )
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].page).is_equal_to(1)


def test_citations_from_nodes__get_content__used_when_no_text() -> None:
    node = SimpleNamespace(
        text=None,
        metadata={"filename": "a.pdf"},
        get_content=lambda: "content from getter",
    )
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].snippet).is_equal_to("content from getter")


def test_citations_from_nodes__no_metadata_keys__unknown_file() -> None:
    node = SimpleNamespace(text="body", metadata={})
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].file_name).is_equal_to(UNKNOWN_FILE_NAME)
    assert_that(citations[0].page).is_none()


def test_citations_from_nodes__invalid_page__skipped() -> None:
    node = SimpleNamespace(
        text="body",
        metadata={"file_name": "a.pdf", "page_label": "not-a-number", "page": 2},
    )
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].page).is_equal_to(2)


def test_citations_from_nodes__page_type_error__skipped() -> None:
    node = SimpleNamespace(
        text="body",
        metadata={"file_name": "a.pdf", "page_label": object(), "page_number": 4},
    )
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].page).is_equal_to(4)


def test_citations_from_nodes__no_text_or_getter__empty_snippet() -> None:
    node = SimpleNamespace(text=None, metadata={"file_name": "a.pdf"})
    citations = citations_from_nodes(nodes=[node])
    assert_that(citations[0].snippet).is_equal_to("")


def test_citations_from_nodes__long_text__truncates() -> None:
    node = SimpleNamespace(text="word " * 200, metadata={"file_name": "long.pdf"})
    citations = citations_from_nodes(nodes=[node], max_snippet_chars=40)
    assert_that(len(citations[0].snippet)).is_less_than_or_equal_to(40)
    assert_that(citations[0].snippet).ends_with("…")


def test_format_citations__empty__returns_empty_string() -> None:
    assert_that(format_citations(citations=[])).is_equal_to("")


def test_format_citations__list__markdown_bullets() -> None:
    citations = [
        Citation(
            file_name="a.pdf",
            page=2,
            score=0.5,
            snippet="snippet one",
        ),
        Citation(
            file_name="b.pdf",
            page=None,
            score=None,
            snippet="snippet two",
        ),
    ]
    markdown = format_citations(citations=citations)
    assert_that(markdown).contains("**a.pdf**")
    assert_that(markdown).contains("p.2")
    assert_that(markdown).contains("score=0.500")
    assert_that(markdown).contains("**b.pdf**")
    assert_that(markdown).contains("snippet two")
