"""Launch the Langflow studio in an isolated uv tool env (no Docker)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Final

from rag.core.config import find_repo_root, load_repo_dotenv

_HOST: Final = "127.0.0.1"
_PORT: Final = "7860"
_CONFIG_DIR_ENV: Final = "LANGFLOW_CONFIG_DIR"
_SAVE_DB_ENV: Final = "LANGFLOW_SAVE_DB_IN_CONFIG_DIR"


def main(*, argv: list[str] | None = None) -> int:
    """Start Langflow via ``uv tool run`` on port 7860.

    Parameters
    ----------
    argv :
        Extra args forwarded to ``langflow run``. Defaults to ``sys.argv[1:]``.

    Returns
    -------
    int
        Process exit code from uv / Langflow.

    Raises
    ------
    SystemExit
        If ``uv`` is not on ``PATH``.
    """
    extra = list(sys.argv[1:] if argv is None else argv)
    uv = shutil.which("uv")
    if uv is None:
        print("❌ uv not found on PATH", file=sys.stderr)
        return 1
    load_repo_dotenv()
    root = find_repo_root()
    config_dir = root / ".data" / "langflow"
    papers_dir = root / "assets" / "pdf" / "papers"
    config_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault(_CONFIG_DIR_ENV, str(config_dir))
    env.setdefault(_SAVE_DB_ENV, "true")
    cmd = [
        uv,
        "tool",
        "run",
        "--from",
        "langflow",
        "langflow",
        "run",
        "--host",
        _HOST,
        "--port",
        _PORT,
        *extra,
    ]
    print("🌊 Langflow studio (isolated uv tool, not the papers-rag venv)")
    print(f"   UI:     http://{_HOST}:{_PORT}")
    print(f"   data:   {config_dir}")
    print(f"   papers: {papers_dir}")
    print("   first start may take a few minutes (downloads Langflow).")
    return subprocess.call(cmd, cwd=root, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
