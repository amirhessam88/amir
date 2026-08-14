"""Tests for Chroma collection reset helper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core.config import RagConfig
from rag.core.ingest import _reset_collection


def test_reset_collection__deletes_then_creates(tmp_path: Path) -> None:
    config = RagConfig(
        papers_dir=tmp_path,
        chroma_dir=tmp_path / "chroma",
        collection_name="papers",
    )
    fake_client = MagicMock()
    fake_collection = MagicMock(name="collection")
    fake_client.get_or_create_collection.return_value = fake_collection

    with patch("rag.core.ingest.chromadb.PersistentClient", return_value=fake_client):
        collection = _reset_collection(config=config)

    fake_client.delete_collection.assert_called_once_with(name="papers")
    fake_client.get_or_create_collection.assert_called_once_with(name="papers")
    assert_that(collection).is_equal_to(fake_collection)


def test_reset_collection__missing_delete__still_creates(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_client = MagicMock()
    fake_client.delete_collection.side_effect = ValueError("missing")
    fake_collection = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection

    with patch("rag.core.ingest.chromadb.PersistentClient", return_value=fake_client):
        collection = _reset_collection(config=config)

    assert_that(collection).is_equal_to(fake_collection)
