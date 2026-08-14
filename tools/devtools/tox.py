"""Run the tox matrix for the monorepo."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _ROOT / "tools" / "resources" / "tox.ini"


def main(*, argv: list[str] | None = None) -> int:
    """Invoke tox with optional passthrough args.

    Parameters
    ----------
    argv :
        Extra CLI args. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code from tox.
    """
    extra = list(sys.argv[1:] if argv is None else argv)
    cmd = [
        sys.executable,
        "-m",
        "tox",
        "-c",
        str(_CONFIG),
        *extra,
    ]
    return subprocess.call(cmd, cwd=_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
