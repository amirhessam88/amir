"""Click CLI for ingesting papers into a strategy-scoped Chroma index."""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import click
from rich.console import Console

from rag.core import RagConfig, RagStrategy, ingest_papers
from rag.core.backends.protocol import IngestNotSupportedError
from rag.core.config import find_repo_root, load_repo_dotenv
from rag.core.strategy import INGEST_ALL, index_dir_for

console = Console()

_STRATEGY_CHOICES = (
    *(item.value for item in RagStrategy.ingestible()),
    INGEST_ALL,
)


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--rebuild/--no-rebuild",
    default=True,
    show_default=True,
    help="Delete and recreate the Chroma collection before ingest.",
)
@click.option(
    "--papers-dir",
    type=click.Path(exists=True, file_okay=False, path_type=str),
    default=None,
    help="Override PAPERS_DIR / default assets/pdf/papers.",
)
@click.option(
    "--chroma-dir",
    type=click.Path(file_okay=False, path_type=str),
    default=None,
    help="Override CHROMA_DIR / default .data/indexes/<strategy>.",
)
@click.option(
    "--strategy",
    type=click.Choice(_STRATEGY_CHOICES, case_sensitive=False),
    default=RagStrategy.LLAMAINDEX.value,
    show_default=True,
    help="Orchestration backend, or 'all' to ingest LlamaIndex and LangChain.",
)
def main(
    *,
    rebuild: bool,
    papers_dir: str | None,
    chroma_dir: str | None,
    strategy: str,
) -> None:
    """Ingest research PDFs into a local Chroma papers index."""
    load_repo_dotenv()
    if strategy == INGEST_ALL:
        if chroma_dir is not None:
            console.print(
                "[red]❌ --chroma-dir cannot be combined with --strategy all "
                "(each backend needs its own persist dir).[/red]",
            )
            sys.exit(1)
        root = find_repo_root()
        base = RagConfig.from_env()
        if papers_dir is not None:
            base = replace(base, papers_dir=Path(papers_dir))
        exit_code = 0
        for item in RagStrategy.ingestible():
            config = replace(
                base,
                strategy=item,
                chroma_dir=index_dir_for(repo_root=root, strategy=item),
            )
            if not _run_ingest(config=config, rebuild=rebuild):
                exit_code = 1
        sys.exit(exit_code)

    chosen = RagStrategy(strategy)
    config = RagConfig.from_env(strategy=chosen)
    if papers_dir is not None or chroma_dir is not None:
        config = replace(
            config,
            papers_dir=Path(papers_dir) if papers_dir else config.papers_dir,
            chroma_dir=Path(chroma_dir) if chroma_dir else config.chroma_dir,
        )
    if not _run_ingest(config=config, rebuild=rebuild):
        sys.exit(1)


def _run_ingest(*, config: RagConfig, rebuild: bool) -> bool:
    """Run one ingest and print status. Return True on success."""
    console.print("📄 [bold]papers-ingest[/bold] starting…")
    console.print(f"   strategy: {config.strategy.value}")
    console.print(f"   papers: {config.papers_dir}")
    console.print(f"   chroma: {config.chroma_dir}")
    console.print(f"   embed:  {config.embed_model_name}")
    console.print(f"   rebuild: {rebuild}")

    try:
        result = ingest_papers(config=config, rebuild=rebuild)
    except IngestNotSupportedError as exc:
        console.print(f"[red]❌ Ingest failed:[/red] {exc}")
        return False
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        console.print(f"[red]❌ Ingest failed:[/red] {exc}")
        return False

    console.print(
        f"✅ Ingested [bold]{result.documents}[/bold] documents → "
        f"[bold]{result.nodes}[/bold] chunks "
        f"into collection [cyan]{result.collection_name}[/cyan]",
    )
    return True


if __name__ == "__main__":
    main()
