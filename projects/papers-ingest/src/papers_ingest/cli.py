"""Click CLI for ingesting papers into Chroma."""

from __future__ import annotations

import sys

import click
from rich.console import Console

from rag.core import RagConfig, ingest_papers
from rag.core.config import load_repo_dotenv

console = Console()


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
    help="Override CHROMA_DIR / default .data/chroma/papers.",
)
def main(*, rebuild: bool, papers_dir: str | None, chroma_dir: str | None) -> None:
    """Ingest research PDFs into the local Chroma papers index."""
    load_repo_dotenv()
    config = RagConfig.from_env()
    if papers_dir is not None:
        from pathlib import Path

        config = RagConfig(
            papers_dir=Path(papers_dir),
            chroma_dir=Path(chroma_dir) if chroma_dir else config.chroma_dir,
            collection_name=config.collection_name,
            embed_model_name=config.embed_model_name,
            llm_model_name=config.llm_model_name,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            similarity_top_k=config.similarity_top_k,
        )
    elif chroma_dir is not None:
        from pathlib import Path

        config = RagConfig(
            papers_dir=config.papers_dir,
            chroma_dir=Path(chroma_dir),
            collection_name=config.collection_name,
            embed_model_name=config.embed_model_name,
            llm_model_name=config.llm_model_name,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            similarity_top_k=config.similarity_top_k,
        )

    console.print("📄 [bold]papers-ingest[/bold] starting…")
    console.print(f"   papers: {config.papers_dir}")
    console.print(f"   chroma: {config.chroma_dir}")
    console.print(f"   embed:  {config.embed_model_name}")
    console.print(f"   rebuild: {rebuild}")

    try:
        result = ingest_papers(config=config, rebuild=rebuild)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        console.print(f"[red]❌ Ingest failed:[/red] {exc}")
        sys.exit(1)

    console.print(
        f"✅ Ingested [bold]{result.documents}[/bold] documents → "
        f"[bold]{result.nodes}[/bold] chunks "
        f"into collection [cyan]{result.collection_name}[/cyan]",
    )


if __name__ == "__main__":
    main()
