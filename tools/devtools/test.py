"""Run the default unit-test suite via pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_PYTEST_INI = _ROOT / "tools" / "resources" / "pytest.ini"
_COVERAGERC = _ROOT / "tools" / "resources" / ".coveragerc"


def main(*, argv: list[str] | None = None) -> int:
    """Run pytest with coverage; skip slow / API / embed markers.

    Parameters
    ----------
    argv :
        Extra pytest args appended after the defaults.
        Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code from pytest.
    """
    extra = list(sys.argv[1:] if argv is None else argv)
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-c",
        str(_PYTEST_INI),
        "--rootdir",
        str(_ROOT),
        "--cov=amir",
        "--cov=rag.core",
        "--cov=papers_rag",
        "--cov=papers_ingest",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        f"--cov-config={_COVERAGERC}",
        "--tb=short",
        "-ra",
        "-v",
        "-m",
        "not slow and not needs_openai and not needs_embed",
        *extra,
    ]
    return subprocess.call(cmd, cwd=_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
