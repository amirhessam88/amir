"""Heuristics to skip figure-dump and boilerplate PDF text."""

from __future__ import annotations

import re
from typing import Final

MIN_PROSE_CHARS: Final = 120
MIN_REAL_WORDS: Final = 8
MAX_SALAD_RATIO: Final = 0.10
MAX_GLUED_RATIO: Final = 0.04
MAX_SNAKE_RATIO: Final = 0.03
MAX_SINGLE_LETTER_RATIO: Final = 0.07
MIN_WORDS_IF_SPARSE: Final = 80
MIN_STUTTER_TOKEN_CHARS: Final = 8

_REAL_WORD_RE = re.compile(r"[A-Za-z]{4,}")
_GLUED_TITLECASE_RE = re.compile(r"(?:[A-Z][a-z]+){3,}")
_CAMEL_RE = re.compile(r"[a-z][A-Z]")
_LETTER_STUTTER_RE = re.compile(r"([A-Za-z])\1{3,}")
_SAFE_TOKEN_CHARS: Final = ".,;:%'()/-_"


def is_prose_text(*, text: str) -> bool:
    """Return True when text looks like readable paper prose.

    Drops short dedications, chart-axis dumps, pyLDAvis chrome, and PDF
    ``/uni00`` figure encodings that pypdf extracts as glyph salad.

    Parameters
    ----------
    text : str
        Extracted page or chunk text.

    Returns
    -------
    bool
        True when the text is worth indexing or citing.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) < MIN_PROSE_CHARS:
        return False
    if "/uni00" in collapsed:
        return False
    tokens = collapsed.split()
    ntok = len(tokens)
    real_words = _REAL_WORD_RE.findall(collapsed)
    if len(real_words) < MIN_REAL_WORDS:
        return False
    salad = 0
    glued = 0
    singles = 0
    snake = 0
    for token in tokens:
        if "_" in token:
            snake += 1
        if len(token) == 1 and token.isalpha():
            singles += 1
        if _GLUED_TITLECASE_RE.search(token) or _CAMEL_RE.search(token):
            glued += 1
        if len(token) >= MIN_STUTTER_TOKEN_CHARS and _LETTER_STUTTER_RE.search(token) is not None:
            return False
        if _is_salad_token(token=token):
            salad += 1
    if salad / ntok >= MAX_SALAD_RATIO:
        return False
    if glued / ntok >= MAX_GLUED_RATIO:
        return False
    if snake / ntok >= MAX_SNAKE_RATIO:
        return False
    return not (singles / ntok >= MAX_SINGLE_LETTER_RATIO and len(real_words) < MIN_WORDS_IF_SPARSE)


def _is_salad_token(*, token: str) -> bool:
    """Return True when a token mixes letters with unusual symbols."""
    if not any(char.isalpha() for char in token):
        return False
    return any(not (char.isalnum() or char in _SAFE_TOKEN_CHARS) for char in token)
