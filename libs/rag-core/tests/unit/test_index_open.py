"""Tests for open_chroma_collection."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core.config import RagConfig
from rag.core.index import open_chroma_collection


def test_open_chroma_collection__creates_client(tmp_path: Path) -> None:
    config = RagConfig(
        papers_dir=tmp_path,
        chroma_dir=tmp_path / "chroma",
        collection_name="papers",
    )
    fake_client = MagicMock()
    fake_collection = MagicMock(name="collection")
    fake_client.get_or_create_collection.return_value = fake_collection

    with patch("rag.core.index.chromadb.PersistentClient", return_value=fake_client) as client_cls:
        collection = open_chroma_collection(config=config)
        client_cls.assert_called_once_with(path=str(config.chroma_dir))
        fake_client.get_or_create_collection.assert_called_once_with(name="papers")
        assert_that(collection).is_equal_to(fake_collection)
        assert_that(config.chroma_dir.is_dir()).is_true()
