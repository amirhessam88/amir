"""Citation helpers for retrieved LlamaIndex nodes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final


class FileMetadataKey(StrEnum):
    """LlamaIndex / loader metadata keys that may hold a file path or name."""

    FILE_NAME = "file_name"
    FILENAME = "filename"
    FILE_PATH = "file_path"
    SOURCE = "source"


class PageMetadataKey(StrEnum):
    """LlamaIndex / pypdf metadata keys that may hold a page number."""

    PAGE_LABEL = "page_label"
    PAGE = "page"
    PAGE_NUMBER = "page_number"


UNKNOWN_FILE_NAME: Final = "unknown"
DEFAULT_SNIPPET_CHARS: Final = 280


@dataclass(frozen=True, kw_only=True)
class Citation:
    """A single retrieved source used to ground an answer.

    Attributes
    ----------
    file_name : str
        PDF file name (or path basename).
    page : int or None
        1-based page number when available.
    score : float or None
        Retriever score when available.
    snippet : str
        Short text excerpt from the chunk.
    """

    file_name: str
    page: int | None
    score: float | None
    snippet: str


def _file_name_from_metadata(*, metadata: dict[str, Any]) -> str:
    """Extract a human-readable file name from node metadata."""
    for key in FileMetadataKey:
        value = metadata.get(key.value)
        if value:
            return Path(str(value)).name
    return UNKNOWN_FILE_NAME


def _page_from_metadata(*, metadata: dict[str, Any]) -> int | None:
    """Extract a 1-based page number from node metadata when present."""
    for key in PageMetadataKey:
        value = metadata.get(key.value)
        if value is None:
            continue
        try:
            page = int(value)
        except (TypeError, ValueError):
            continue
        # LlamaIndex / pypdf often use 0-based page; keep label as-is if >= 1
        return page if page >= 1 else page + 1
    return None


def _snippet(*, text: str, max_chars: int = DEFAULT_SNIPPET_CHARS) -> str:
    """Collapse whitespace and truncate for UI display."""
    collapsed = " ".join(text.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 1].rstrip() + "…"


def citations_from_nodes(
    *,
    nodes: Sequence[Any],
    max_snippet_chars: int = DEFAULT_SNIPPET_CHARS,
) -> list[Citation]:
    """Convert LlamaIndex ``NodeWithScore`` objects into citations.

    Parameters
    ----------
    nodes : Sequence
        Retrieved nodes (typically ``NodeWithScore``).
    max_snippet_chars : int
        Max characters for each snippet.

    Returns
    -------
    list of Citation
        Ordered citations matching retrieval order.
    """
    citations: list[Citation] = []
    for item in nodes:
        node = getattr(item, "node", item)
        metadata = dict(getattr(node, "metadata", {}) or {})
        text = _node_text(node=node)
        score_raw = getattr(item, "score", None)
        score = float(score_raw) if score_raw is not None else None
        citations.append(
            Citation(
                file_name=_file_name_from_metadata(metadata=metadata),
                page=_page_from_metadata(metadata=metadata),
                score=score,
                snippet=_snippet(text=text, max_chars=max_snippet_chars),
            ),
        )
    return citations


def _node_text(*, node: Any) -> str:
    """Best-effort text extraction from a LlamaIndex node-like object."""
    raw = getattr(node, "text", None)
    if raw:
        return str(raw)
    get_content = getattr(node, "get_content", None)
    if callable(get_content):
        return str(get_content())
    return ""


def format_citations(*, citations: Sequence[Citation]) -> str:
    """Render citations as a markdown bullet list.

    Parameters
    ----------
    citations : Sequence of Citation
        Citations to format.

    Returns
    -------
    str
        Markdown string (empty when there are no citations).
    """
    if not citations:
        return ""
    lines: list[str] = []
    for index, citation in enumerate(citations, start=1):
        page_part = f", p.{citation.page}" if citation.page is not None else ""
        score_part = f" (score={citation.score:.3f})" if citation.score is not None else ""
        lines.append(
            f"{index}. **{citation.file_name}**{page_part}{score_part} — {citation.snippet}",
        )
    return "\n".join(lines)
