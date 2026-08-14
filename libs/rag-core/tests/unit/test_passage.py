"""Tests for author-question / acknowledgement passage helpers."""

from assertpy import assert_that

from rag.core.passage import (
    is_acknowledgement_text,
    is_author_question,
    is_proceedings_boilerplate_text,
    page_from_mapping,
)


def test_is_author_question__cues() -> None:
    assert_that(is_author_question(question="who is the main author")).is_true()
    assert_that(is_author_question(question="What is a driver node?")).is_false()
    assert_that(is_author_question(question="What did the authors conclude?")).is_false()


def test_is_acknowledgement_text__revision_thanks() -> None:
    thanks = "Tessa Daniels for the careful revision of the manuscript."
    authors = "Amirhessam Tahmassebi, Katja Pinker-Domenig, Anke Meyer-Baese"
    assert_that(is_acknowledgement_text(text=thanks)).is_true()
    assert_that(is_acknowledgement_text(text=authors)).is_false()


def test_is_proceedings_boilerplate_text__spie_editors() -> None:
    footer = (
        "Smart Biomedical and Physiological Sensor Technology XIV, edited by "
        "Brian M. Cullum, Douglas Kiehl, Eric S. McLamore, Proc. of SPIE Vol. 10216"
    )
    title = "Amirhessam Tahmassebi, Katja Pinker-Domenig, Anke Meyer-Baese wrote this."
    assert_that(is_proceedings_boilerplate_text(text=footer)).is_true()
    assert_that(is_proceedings_boilerplate_text(text=title)).is_false()


def test_page_from_mapping__parses_and_skips() -> None:
    assert_that(page_from_mapping(metadata={"page": 2})).is_equal_to(2)
    assert_that(page_from_mapping(metadata={"page": 0})).is_equal_to(1)
    assert_that(page_from_mapping(metadata={"page_label": "4"})).is_equal_to(4)
    assert_that(page_from_mapping(metadata={"page": "x"})).is_none()
    assert_that(page_from_mapping(metadata={"page": []})).is_none()
    assert_that(page_from_mapping(metadata={})).is_none()
