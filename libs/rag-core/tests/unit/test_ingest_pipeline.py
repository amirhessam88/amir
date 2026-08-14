"""Mocked ingest pipeline tests (no HuggingFace download)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from assertpy import assert_that

from rag.core.config import RagConfig
from rag.core.ingest import IngestResult, build_embed_model, ingest_papers


def test_build_embed_model__passes_name(tmp_path: Path) -> None:
    config = RagConfig(
        papers_dir=tmp_path,
        chroma_dir=tmp_path / "chroma",
        embed_model_name="fake/model",
    )
    with patch("rag.core.ingest.HuggingFaceEmbedding") as hf:
        hf.return_value = MagicMock(name="embed")
        model = build_embed_model(config=config)
        hf.assert_called_once_with(model_name="fake/model")
        assert_that(model).is_equal_to(hf.return_value)


def test_ingest_papers__rebuild__writes_collection(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF-1.4")
    chroma = tmp_path / "chroma"
    config = RagConfig(papers_dir=papers, chroma_dir=chroma, collection_name="papers")

    fake_collection = MagicMock()
    fake_collection.count.return_value = 2
    fake_docs = [MagicMock(), MagicMock()]
    fake_index = MagicMock()

    with (
        patch("rag.core.ingest._reset_collection", return_value=fake_collection),
        patch("rag.core.ingest.ChromaVectorStore") as store_cls,
        patch("rag.core.ingest.StorageContext.from_defaults") as storage_cls,
        patch("rag.core.ingest.load_pdf_documents", return_value=fake_docs),
        patch("rag.core.ingest.VectorStoreIndex.from_documents", return_value=fake_index),
        patch("rag.core.ingest.Settings"),
        patch("rag.core.ingest.SentenceSplitter"),
    ):
        store_cls.return_value = MagicMock()
        storage_cls.return_value = MagicMock()
        embed = MagicMock()

        result = ingest_papers(config=config, embed_model=embed, rebuild=True)

        assert_that(result).is_instance_of(IngestResult)
        assert_that(result.documents).is_equal_to(2)
        assert_that(result.nodes).is_equal_to(2)
        assert_that(result.collection_name).is_equal_to("papers")


def test_ingest_papers__append__uses_get_or_create(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF-1.4")
    config = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "chroma")

    fake_collection = MagicMock()
    fake_collection.count.return_value = 1
    fake_client = MagicMock()
    fake_client.get_or_create_collection.return_value = fake_collection

    with (
        patch("rag.core.ingest.chromadb.PersistentClient", return_value=fake_client),
        patch("rag.core.ingest.ChromaVectorStore"),
        patch("rag.core.ingest.StorageContext.from_defaults"),
        patch("rag.core.ingest.load_pdf_documents", return_value=[MagicMock()]),
        patch("rag.core.ingest.VectorStoreIndex.from_documents"),
        patch("rag.core.ingest.Settings"),
        patch("rag.core.ingest.SentenceSplitter"),
    ):
        result = ingest_papers(config=config, embed_model=MagicMock(), rebuild=False)
        fake_client.get_or_create_collection.assert_called_once()
        assert_that(result.documents).is_equal_to(1)
