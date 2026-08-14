"""Unit tests for index loading error paths."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core.config import RagConfig
from rag.core.index import IndexMissingError, load_vector_index


def test_load_vector_index__empty_collection__raises(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_collection = MagicMock()
    fake_collection.count.return_value = 0
    embed = MagicMock()

    with patch("rag.core.index.open_chroma_collection", return_value=fake_collection):
        try:
            load_vector_index(
                config=config,
                embed_model=embed,
                require_nonempty=True,
            )
            raise AssertionError("expected IndexMissingError")
        except IndexMissingError as exc:
            assert_that(str(exc)).contains("empty")


def test_load_vector_index__nonempty__builds_index(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path, chroma_dir=tmp_path / "chroma")
    fake_collection = MagicMock()
    fake_collection.count.return_value = 3
    embed = MagicMock()
    fake_index = MagicMock(name="vector-index")

    with (
        patch("rag.core.index.open_chroma_collection", return_value=fake_collection),
        patch("rag.core.index.ChromaVectorStore") as store_cls,
        patch(
            "rag.core.index.VectorStoreIndex.from_vector_store", return_value=fake_index
        ) as from_vs,
    ):
        store_cls.return_value = MagicMock()
        index = load_vector_index(config=config, embed_model=embed)
        assert_that(index).is_equal_to(fake_index)
        from_vs.assert_called_once()
