"""Run ruff format / check for the monorepo."""

from __future__ import annotations

import argparse
import subprocess
import sys
from enum import StrEnum
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CONFIG = _ROOT / "tools" / "resources" / "ruff.toml"


class RuffAction(StrEnum):
    """Supported ruff entrypoints for the monorepo."""

    FORMAT = "format"
    CHECK = "check"


def main(*, argv: list[str] | None = None) -> int:
    """Dispatch ``format`` or ``check`` to ruff.

    Parameters
    ----------
    argv :
        CLI args after the script name. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code from ruff.
    """
    parser = argparse.ArgumentParser(description="Run ruff against the repo root.")
    parser.add_argument(
        "action",
        type=RuffAction,
        choices=list(RuffAction),
        help="ruff subcommand to run",
    )
    args, passthrough = parser.parse_known_args(argv)
    action: RuffAction = args.action
    cmd = [
        sys.executable,
        "-m",
        "ruff",
        action.value,
        str(_ROOT),
        "--config",
        str(_CONFIG),
        *passthrough,
    ]
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
