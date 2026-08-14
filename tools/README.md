# 🧰 tools

Monorepo tool entrypoints and their config. Root [`pyproject.toml`](../pyproject.toml)
`poe` tasks call these files — keep orchestration here, not under `scripts/`.

| Path | Role |
|------|------|
| [`devtools/`](devtools/) | Day-to-day engineer loop (greet, ruff, mypy, test, tox) |
| [`buildtools/`](buildtools/) | Workspace uv helpers, docs site, clean |
| [`resources/`](resources/) | Shared tool configs (`mypy.ini`, `ruff.toml`, `pytest.ini`, …) |

```bash
# monorepo workspace
poe sync                 # uv sync --locked --all-groups --all-packages
poe lock                 # refresh uv.lock (no upgrades)
poe upgrade              # upgrade all locked deps, then sync
poe upgrade ruff mypy    # upgrade selected packages only, then sync
poe verify               # check + test

# engineer loop
poe format               # → ruff format + ruff check --fix
poe check                # → greet + ruff + mypy
poe test                 # → tools/devtools/test.py (all leaves)
poe docs                 # → tools/buildtools/docs.py
poe clean                # → tools/buildtools/clean.py
```
