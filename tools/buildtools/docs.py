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


def _run_sphinx(*, docs_dir: Path, out_dir: Path) -> None:
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

    for docs_dir, name in LEAVES:
        if not (docs_dir / "conf.py").is_file():
            print(f"⚠️  skip {name}: no conf.py in {docs_dir}")
            continue
        _run_sphinx(docs_dir=docs_dir, out_dir=SITE / name)

    print(f"✅ docs site ready at {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
