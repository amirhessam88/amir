"""Remove ignored caches, coverage, build, and docs artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Top-level paths removed wholesale when present.
_TOP_LEVEL: tuple[str, ...] = (
    ".coverage",
    "dist",
    "build",
    "site",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "htmlcov",
    "xmlcov",
)

# Glob patterns matched anywhere under the repo root.
_GLOBS: tuple[str, ...] = (
    ".coverage.*",
    "**/docs/_build",
    "**/__pycache__",
    "**/.ipynb_checkpoints",
)


def _remove(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"🧹 removed {path.relative_to(ROOT)}")


def main() -> int:
    """Delete local build / cache artifacts under the repo root.

    Returns
    -------
    int
        Always ``0``.
    """
    for name in _TOP_LEVEL:
        _remove(ROOT / name)

    seen: set[Path] = set()
    for pattern in _GLOBS:
        for path in ROOT.glob(pattern):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            _remove(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
