"""Framework-agnostic PDF page loading for ingest backends."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from rag.core.citations import FileMetadataKey, PageMetadataKey
from rag.core.text_quality import is_prose_text


@dataclass(frozen=True, kw_only=True)
class PageDocument:
    """One extractable PDF page.

    Attributes
    ----------
    text : str
        Prose text from the page.
    metadata : dict
        File name, path, and 1-based page fields shared by all backends.
    """

    text: str
    metadata: dict[str, Any]


def list_pdf_paths(*, papers_dir: Path) -> list[Path]:
    """List PDF files under ``papers_dir`` (non-recursive).

    Parameters
    ----------
    papers_dir : Path
        Directory containing PDFs.

    Returns
    -------
    list of Path
        Sorted PDF paths.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist or contains no PDFs.
    """
    if not papers_dir.is_dir():
        raise FileNotFoundError(f"Papers directory not found: {papers_dir}")
    paths = sorted(papers_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"No PDF files found in {papers_dir}")
    return paths


def load_pdf_pages(*, pdf_paths: Sequence[Path]) -> list[PageDocument]:
    """Extract per-page prose from PDFs with pypdf.

    Pages that fail ``is_prose_text`` (figures, dedications, glyph salad) are
    skipped.

    Parameters
    ----------
    pdf_paths : sequence of Path
        PDF files to load.

    Returns
    -------
    list of PageDocument
        One document per extractable page.

    Raises
    ------
    FileNotFoundError
        If no page yields extractable text.
    """
    documents: list[PageDocument] = []
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for index, page in enumerate(reader.pages):
            raw = page.extract_text() or ""
            if not is_prose_text(text=raw):
                continue
            page_number = index + 1
            documents.append(
                PageDocument(
                    text=raw,
                    metadata={
                        FileMetadataKey.FILE_NAME.value: pdf_path.name,
                        FileMetadataKey.FILE_PATH.value: str(pdf_path),
                        PageMetadataKey.PAGE_LABEL.value: str(page_number),
                        PageMetadataKey.PAGE.value: page_number,
                    },
                ),
            )
    if not documents:
        raise FileNotFoundError(
            "No extractable text found in the PDF corpus. "
            "Check that the files are text PDFs, not image-only scans.",
        )
    return documents
