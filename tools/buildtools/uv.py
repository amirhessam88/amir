"""uv workspace helpers for the amir monorepo."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from enum import StrEnum
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


class UvAction(StrEnum):
    """Supported uv workspace actions."""

    SYNC = "sync"
    LOCK = "lock"
    UPGRADE = "upgrade"


def _uv() -> str:
    uv = shutil.which("uv")
    if uv is None:
        print("❌ uv not found on PATH", file=sys.stderr)
        raise SystemExit(1)
    return uv


def _run(*, args: list[str]) -> int:
    display = ["uv", *args[1:]]
    print(f"📦 {' '.join(display)}")
    return subprocess.call(args, cwd=_ROOT)


def _sync(*, locked: bool) -> int:
    cmd = [_uv(), "sync", "--all-groups", "--all-packages"]
    if locked:
        cmd.append("--locked")
    return _run(args=cmd)


def _lock(*, upgrade_all: bool, packages: list[str]) -> int:
    cmd = [_uv(), "lock"]
    if upgrade_all:
        cmd.append("--upgrade")
    for name in packages:
        cmd.extend(["--upgrade-package", name])
    return _run(args=cmd)


def main(*, argv: list[str] | None = None) -> int:
    """Dispatch workspace uv actions.

    Parameters
    ----------
    argv :
        CLI args after the script name. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code from uv.
    """
    parser = argparse.ArgumentParser(
        description="uv workspace sync / lock / upgrade for the monorepo.",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser(UvAction.SYNC.value, help="uv sync --locked --all-groups --all-packages")
    sub.add_parser(UvAction.LOCK.value, help="uv lock (refresh without upgrading)")

    upgrade = sub.add_parser(
        UvAction.UPGRADE.value,
        help="Upgrade lockfile deps (all, or named packages) then sync",
    )
    upgrade.add_argument(
        "packages",
        nargs="*",
        help="Optional package names; omit to upgrade everything",
    )

    args = parser.parse_args(argv)
    action = UvAction(args.action)

    if action is UvAction.SYNC:
        return _sync(locked=True)
    if action is UvAction.LOCK:
        return _lock(upgrade_all=False, packages=[])
    if action is UvAction.UPGRADE:
        packages = list(args.packages)
        code = _lock(upgrade_all=not packages, packages=packages)
        if code != 0:
            return code
        return _sync(locked=False)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
