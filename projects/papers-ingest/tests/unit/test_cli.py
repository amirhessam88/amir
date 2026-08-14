"""CLI smoke tests with mocked ingest."""

from pathlib import Path
from unittest.mock import patch

from assertpy import assert_that
from click.testing import CliRunner

from papers_ingest.cli import main
from rag.core.backends.protocol import IngestNotSupportedError
from rag.core.config import RagConfig
from rag.core.ingest import IngestResult
from rag.core.strategy import RagStrategy


def test_main__success__exits_zero(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    runner = CliRunner()
    result_obj = IngestResult(
        documents=1,
        nodes=4,
        chroma_dir=tmp_path / "chroma",
        collection_name="papers",
    )
    with patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest:
        result = runner.invoke(
            main,
            ["--papers-dir", str(papers), "--chroma-dir", str(tmp_path / "chroma")],
        )
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("Ingested")
    ingest.assert_called_once()


def test_main__chroma_only_override__exits_zero(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    config = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "default-chroma")
    result_obj = IngestResult(
        documents=2,
        nodes=8,
        chroma_dir=tmp_path / "chroma-only",
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=config),
    ):
        result = runner.invoke(main, ["--chroma-dir", str(tmp_path / "chroma-only")])
    assert_that(result.exit_code).is_equal_to(0)
    called_config = ingest.call_args.kwargs["config"]
    assert_that(called_config.chroma_dir).is_equal_to(tmp_path / "chroma-only")
    assert_that(called_config.papers_dir).is_equal_to(papers)


def test_main__papers_dir_keeps_default_chroma(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    default_chroma = tmp_path / "default-chroma"
    config = RagConfig(papers_dir=tmp_path / "ignored", chroma_dir=default_chroma)
    result_obj = IngestResult(
        documents=1,
        nodes=1,
        chroma_dir=default_chroma,
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=config),
    ):
        result = runner.invoke(main, ["--papers-dir", str(papers), "--no-rebuild"])
    assert_that(result.exit_code).is_equal_to(0)
    called = ingest.call_args.kwargs
    assert_that(called["rebuild"]).is_false()
    assert_that(called["config"].papers_dir).is_equal_to(papers)
    assert_that(called["config"].chroma_dir).is_equal_to(default_chroma)


def test_main__defaults_from_env__exits_zero(tmp_path: Path) -> None:
    config = RagConfig(papers_dir=tmp_path / "papers", chroma_dir=tmp_path / "chroma")
    (tmp_path / "papers").mkdir()
    result_obj = IngestResult(
        documents=0,
        nodes=0,
        chroma_dir=config.chroma_dir,
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=config),
    ):
        result = runner.invoke(main, [])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(ingest.call_args.kwargs["config"]).is_equal_to(config)


def test_main__strategy_flag__passed_to_config(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    config = RagConfig(
        papers_dir=papers,
        chroma_dir=tmp_path / "lc",
        strategy=RagStrategy.LANGCHAIN,
    )
    result_obj = IngestResult(
        documents=1,
        nodes=1,
        chroma_dir=config.chroma_dir,
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=config),
    ):
        result = runner.invoke(main, ["--strategy", "langchain", "--papers-dir", str(papers)])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(result.output).contains("langchain")
    ingest.assert_called_once()


def test_main__strategy_all__runs_ingestible(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    base = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "ignored")
    result_obj = IngestResult(
        documents=1,
        nodes=1,
        chroma_dir=tmp_path / "x",
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=base),
        patch("papers_ingest.cli.find_repo_root", return_value=tmp_path),
    ):
        result = runner.invoke(main, ["--strategy", "all", "--papers-dir", str(papers)])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(ingest.call_count).is_equal_to(2)


def test_main__strategy_all_with_chroma_dir__exits_one(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--strategy", "all", "--chroma-dir", str(tmp_path / "one")],
    )
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("--chroma-dir")


def test_main__failure__exits_one(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    runner = CliRunner()
    with patch("papers_ingest.cli.ingest_papers", side_effect=RuntimeError("boom")):
        result = runner.invoke(main, ["--papers-dir", str(papers)])
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("Ingest failed")


def test_main__ingest_not_supported__exits_one(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    runner = CliRunner()
    with patch(
        "papers_ingest.cli.ingest_papers",
        side_effect=IngestNotSupportedError("studio"),
    ):
        result = runner.invoke(main, ["--papers-dir", str(papers)])
    assert_that(result.exit_code).is_equal_to(1)
    assert_that(result.output).contains("studio")


def test_main__strategy_all__without_papers_dir(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    base = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "ignored")
    result_obj = IngestResult(
        documents=1,
        nodes=1,
        chroma_dir=tmp_path / "x",
        collection_name="papers",
    )
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", return_value=result_obj) as ingest,
        patch("papers_ingest.cli.RagConfig.from_env", return_value=base),
        patch("papers_ingest.cli.find_repo_root", return_value=tmp_path),
    ):
        result = runner.invoke(main, ["--strategy", "all"])
    assert_that(result.exit_code).is_equal_to(0)
    assert_that(ingest.call_count).is_equal_to(2)


def test_main__strategy_all__failure__exits_one(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "a.pdf").write_bytes(b"%PDF")
    base = RagConfig(papers_dir=papers, chroma_dir=tmp_path / "ignored")
    runner = CliRunner()
    with (
        patch("papers_ingest.cli.ingest_papers", side_effect=RuntimeError("boom")),
        patch("papers_ingest.cli.RagConfig.from_env", return_value=base),
        patch("papers_ingest.cli.find_repo_root", return_value=tmp_path),
    ):
        result = runner.invoke(main, ["--strategy", "all", "--papers-dir", str(papers)])
    assert_that(result.exit_code).is_equal_to(1)
