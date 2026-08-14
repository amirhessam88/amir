"""Run mypy for the monorepo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _ROOT / "tools" / "resources" / "mypy.ini"
_TARGETS = (
    _ROOT / "src",
    _ROOT / "libs" / "rag-core" / "src",
    _ROOT / "apps" / "papers-rag" / "src",
    _ROOT / "projects" / "papers-ingest" / "src",
    _ROOT / "tools",
)


def main(*, argv: list[str] | None = None) -> int:
    """Invoke mypy with optional passthrough args.

    Parameters
    ----------
    argv :
        Extra CLI args. Defaults to ``sys.argv[1:]``.
        When empty, checks the default monorepo source trees.

    Returns
    -------
    int
        Process exit code from mypy.
    """
    extra = list(sys.argv[1:] if argv is None else argv)
    targets = [str(path) for path in _TARGETS] if not extra else []
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--config-file",
        str(_CONFIG),
        *targets,
        *extra,
    ]
    return subprocess.call(cmd, cwd=_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
