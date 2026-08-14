"""Passage selection helpers shared by RAG backends."""

from __future__ import annotations

from typing import Any, Final

from rag.core.citations import PageMetadataKey

AUTHOR_QUESTION_CUES: Final = (
    "who wrote",
    "who is the writer",
    "who is the author",
    "who are the authors",
    "who is the main author",
    "main author",
    "first author",
    "corresponding author",
    "list the authors",
    "authors of",
)

ACKNOWLEDGEMENT_CUES: Final = (
    "acknowledg",
    "thanks to",
    "thank ",
    "grateful to",
    "careful revision",
    "revising the manuscript",
    "revision of the manuscript",
)

PROCEEDINGS_BOILERPLATE_CUES: Final = (
    "edited by",
    "proc. of spie",
    "ccc code",
    "spiedigitallibrary",
    "terms of use",
)

QA_GROUNDING_RULES: Final = (
    "People thanked for revising a manuscript are not authors. "
    "SPIE 'edited by' names are volume editors, not the paper's authors. "
    "Prefer names on a title page or an explicit author list. "
    "If several papers appear, do not pick one 'main author' for the whole "
    "library — list authors per filename."
)


def is_author_question(*, question: str) -> bool:
    """Return True when the question is asking who wrote a paper.

    Parameters
    ----------
    question : str
        User question.

    Returns
    -------
    bool
        True when authorship cues are present.
    """
    lowered = " ".join(question.lower().split())
    return any(cue in lowered for cue in AUTHOR_QUESTION_CUES)


def is_acknowledgement_text(*, text: str) -> bool:
    """Return True when text looks like thanks / manuscript revision notes.

    Parameters
    ----------
    text : str
        Chunk or page text.

    Returns
    -------
    bool
        True when acknowledgement phrasing dominates authorship lists.
    """
    lowered = text.lower()
    return any(cue in lowered for cue in ACKNOWLEDGEMENT_CUES)


def is_proceedings_boilerplate_text(*, text: str) -> bool:
    """Return True when text is SPIE copyright / volume-editor footer.

    Parameters
    ----------
    text : str
        Chunk or page text.

    Returns
    -------
    bool
        True when proceedings chrome is present.
    """
    lowered = text.lower()
    return any(cue in lowered for cue in PROCEEDINGS_BOILERPLATE_CUES)


def page_from_mapping(*, metadata: dict[str, Any]) -> int | None:
    """Read a 1-based page number from chunk metadata.

    Parameters
    ----------
    metadata : dict
        Loader metadata.

    Returns
    -------
    int or None
        Page number when parseable.
    """
    for key in PageMetadataKey:
        value = metadata.get(key.value)
        if value is None:
            continue
        try:
            page = int(value)
        except (TypeError, ValueError):
            continue
        return page if page >= 1 else page + 1
    return None
