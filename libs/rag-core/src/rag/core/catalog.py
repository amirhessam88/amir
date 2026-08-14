"""Paper catalog and corpus-vs-paper query routing."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

from rag.core.citations import FileMetadataKey
from rag.core.config import RagConfig

CATALOG_FILE_NAME: Final = "catalog.json"
TITLE_SNIPPET_CHARS: Final = 220

_CORPUS_CUES: Final = (
    "all papers",
    "all the papers",
    "every paper",
    "entire corpus",
    "the corpus",
    "among all",
    "across all",
    "common topic among",
    "main topic among",
    "common theme",
    "unifying theme",
    "body of work",
    "what do these papers",
    "these papers have in common",
    "theme across",
    "overall research",
)


class QueryScope(StrEnum):
    """Whether a question is about one paper or the whole corpus."""

    PAPER = "paper"
    CORPUS = "corpus"


class CatalogJsonKey(StrEnum):
    """Keys in the on-disk catalog JSON object."""

    PAPERS = "papers"
    FILE_NAME = "file_name"
    TITLE = "title"


@dataclass(frozen=True, kw_only=True)
class PaperCatalogEntry:
    """One PDF in the corpus catalog.

    Attributes
    ----------
    file_name : str
        PDF basename.
    title : str
        Opening-page snippet used as a title stand-in.
    """

    file_name: str
    title: str


@dataclass(frozen=True, kw_only=True)
class PaperCatalog:
    """Ordered catalog of ingested papers.

    Attributes
    ----------
    papers : tuple of PaperCatalogEntry
        One entry per PDF, typically ingest order.
    """

    papers: tuple[PaperCatalogEntry, ...]

    def to_markdown(self) -> str:
        """Render the catalog as a markdown bullet list."""
        if not self.papers:
            return ""
        lines: list[str] = []
        for entry in self.papers:
            title = entry.title.strip()
            suffix = f" — {title}" if title else ""
            lines.append(f"- **{entry.file_name}**{suffix}")
        return "\n".join(lines)

    def to_json(self) -> str:
        """Serialize the catalog to a JSON string."""
        payload = {
            CatalogJsonKey.PAPERS.value: [
                {
                    CatalogJsonKey.FILE_NAME.value: entry.file_name,
                    CatalogJsonKey.TITLE.value: entry.title,
                }
                for entry in self.papers
            ],
        }
        return json.dumps(payload, indent=2) + "\n"

    @classmethod
    def from_json(cls, raw: str) -> PaperCatalog:
        """Parse a catalog JSON string.

        Parameters
        ----------
        raw : str
            JSON produced by ``to_json``.

        Returns
        -------
        PaperCatalog
            Parsed catalog (empty when ``papers`` is missing).
        """
        data = json.loads(raw)
        rows = data.get(CatalogJsonKey.PAPERS.value, []) if isinstance(data, dict) else []
        papers: list[PaperCatalogEntry] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                name = str(row.get(CatalogJsonKey.FILE_NAME.value, "")).strip()
                if not name:
                    continue
                papers.append(
                    PaperCatalogEntry(
                        file_name=Path(name).name,
                        title=str(row.get(CatalogJsonKey.TITLE.value, "")).strip(),
                    ),
                )
        return cls(papers=tuple(papers))


def classify_query_scope(*, question: str) -> QueryScope:
    """Classify a user question as paper-level or corpus-level.

    Parameters
    ----------
    question : str
        Natural-language question.

    Returns
    -------
    QueryScope
        ``CORPUS`` when the question is about the whole library.
    """
    lowered = " ".join(question.lower().split())
    for cue in _CORPUS_CUES:
        if cue in lowered:
            return QueryScope.CORPUS
    return QueryScope.PAPER


def title_from_text(*, text: str) -> str:
    """Collapse whitespace and truncate opening text for the catalog.

    Parameters
    ----------
    text : str
        First extractable page (or any snippet).

    Returns
    -------
    str
        Short title stand-in.
    """
    collapsed = " ".join(text.split())
    if len(collapsed) <= TITLE_SNIPPET_CHARS:
        return collapsed
    return collapsed[: TITLE_SNIPPET_CHARS - 1].rstrip() + "…"


def catalog_from_documents(
    *,
    pdf_paths: Sequence[Path],
    documents: Sequence[Any],
) -> PaperCatalog:
    """Build a catalog keyed by PDF path, using first-page text when present.

    Parameters
    ----------
    pdf_paths : sequence of Path
        Source PDFs (defines order and completeness).
    documents : sequence
        LlamaIndex documents with ``file_name`` metadata.

    Returns
    -------
    PaperCatalog
        One entry per PDF path.
    """
    titles: dict[str, str] = {}
    for document in documents:
        metadata = getattr(document, "metadata", None)
        if not isinstance(metadata, dict):
            continue
        raw_name = metadata.get(FileMetadataKey.FILE_NAME.value)
        if not raw_name:
            continue
        name = Path(str(raw_name)).name
        if name in titles:
            continue
        text = getattr(document, "text", "") or ""
        titles[name] = title_from_text(text=str(text))
    papers = tuple(
        PaperCatalogEntry(file_name=path.name, title=titles.get(path.name, ""))
        for path in pdf_paths
    )
    return PaperCatalog(papers=papers)


def catalog_path(*, chroma_dir: Path) -> Path:
    """Return the catalog JSON path under the Chroma directory.

    Parameters
    ----------
    chroma_dir : Path
        Persistence directory.

    Returns
    -------
    Path
        ``chroma_dir / catalog.json``.
    """
    return chroma_dir / CATALOG_FILE_NAME


def write_paper_catalog(*, catalog: PaperCatalog, chroma_dir: Path) -> Path:
    """Write ``catalog.json`` next to the Chroma store.

    Parameters
    ----------
    catalog : PaperCatalog
        Catalog to persist.
    chroma_dir : Path
        Persistence directory (created if missing).

    Returns
    -------
    Path
        Path written.
    """
    chroma_dir.mkdir(parents=True, exist_ok=True)
    path = catalog_path(chroma_dir=chroma_dir)
    path.write_text(catalog.to_json(), encoding="utf-8")
    return path


def load_paper_catalog(*, config: RagConfig) -> PaperCatalog:
    """Load the catalog from disk, or filenames from ``papers_dir``.

    Parameters
    ----------
    config : RagConfig
        Provides ``chroma_dir`` and ``papers_dir``.

    Returns
    -------
    PaperCatalog
        Persisted catalog, or a filenames-only fallback.
    """
    path = catalog_path(chroma_dir=config.chroma_dir)
    if path.is_file():
        try:
            return PaperCatalog.from_json(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    from rag.core.ingest import list_pdf_paths

    paths = list_pdf_paths(papers_dir=config.papers_dir)
    return PaperCatalog(
        papers=tuple(PaperCatalogEntry(file_name=path.name, title="") for path in paths),
    )
