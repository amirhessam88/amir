"""Build the docs super-app: landing + portal + every product Sphinx leaf."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / "site"

# (source docs dir, site subdirectory name)
LEAVES: list[tuple[Path, str]] = [
    (ROOT / "libs" / "rag-core" / "docs", "rag-core"),
    (ROOT / "apps" / "papers-rag" / "docs", "papers-rag"),
    (ROOT / "projects" / "papers-ingest" / "docs", "papers-ingest"),
    (ROOT / "tools" / "docs", "toolbox"),
    (ROOT / "docs" / "portal", "architecture"),
]


_LEGACY_ARCHITECTURE_PAGES: tuple[str, ...] = (
    "overview",
    "rag-stack",
    "langflow",
    "toolchain",
)


def _run_sphinx(*, docs_dir: Path, out_dir: Path) -> None:
    """Run Sphinx HTML into ``out_dir``.

    Parameters
    ----------
    docs_dir : Path
        Leaf ``docs/`` directory with ``conf.py``.
    out_dir : Path
        Output directory under ``site/``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "sphinx",
        "-b",
        "html",
        "-q",
        str(docs_dir),
        str(out_dir),
    ]
    print(f"📚 sphinx: {docs_dir.relative_to(ROOT)} → {out_dir.relative_to(ROOT)}")
    subprocess.run(cmd, check=True, cwd=ROOT)


def _redirect_html(*, target: str) -> str:
    """Return a meta-refresh HTML stub for a moved page.

    Parameters
    ----------
    target : str
        Relative URL of the new location.

    Returns
    -------
    str
        Complete HTML document.
    """
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        f'    <meta http-equiv="refresh" content="0; url={target}" />\n'
        f'    <link rel="canonical" href="{target}" />\n'
        "    <title>Moved</title>\n"
        "  </head>\n"
        "  <body>\n"
        f'    <p>Moved to <a href="{target}">{target}</a>.</p>\n'
        "  </body>\n"
        "</html>\n"
    )


def _write_architecture_legacy_redirects(*, out_dir: Path) -> None:
    """Keep old ``/architecture/architecture/*.html`` URLs working.

    Parameters
    ----------
    out_dir : Path
        Sphinx output directory for the architecture portal (``site/architecture``).
    """
    nested = out_dir / "architecture"
    nested.mkdir(parents=True, exist_ok=True)
    for name in _LEGACY_ARCHITECTURE_PAGES:
        target = f"../{name}.html"
        (nested / f"{name}.html").write_text(
            _redirect_html(target=target),
            encoding="utf-8",
        )


def main() -> int:
    """Assemble ``site/`` for GitHub Pages / local preview.

    Returns
    -------
    int
        ``0`` on success, ``1`` if the landing page is missing.
    """
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    landing = ROOT / "docs" / "landing"
    if not (landing / "index.html").is_file():
        print("❌ missing docs/landing/index.html", file=sys.stderr)
        return 1
    for path in landing.iterdir():
        target = SITE / path.name
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)
    print("🏠 copied docs/landing → site/")
    logo = ROOT / "assets" / "img" / "logo_color_clear.png"
    if logo.is_file():
        img_dir = SITE / "img"
        img_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(logo, img_dir / logo.name)
    (SITE / ".nojekyll").touch()

    for docs_dir, name in LEAVES:
        if not (docs_dir / "conf.py").is_file():
            print(f"⚠️  skip {name}: no conf.py in {docs_dir}")
            continue
        _run_sphinx(docs_dir=docs_dir, out_dir=SITE / name)

    _write_architecture_legacy_redirects(out_dir=SITE / "architecture")
    print(f"✅ docs site ready at {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
