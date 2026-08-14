# ⚙️ resources

Shared tool configs live under `tools/resources/`. Entrypoints pass these paths
explicitly so the repo root stays free of `mypy.ini` / `ruff.toml` clutter.

| File | Used by |
|------|---------|
| `mypy.ini` | `tools/devtools/mypy.py` |
| `ruff.toml` | `tools/devtools/ruff.py` |
| `pytest.ini` | `tools/devtools/test.py` |
| `.coveragerc` | `tools/devtools/test.py` (`fail_under = 100`) |
| `tox.ini` | `tools/devtools/tox.py` |

Path settings that resolve relative to the config file use `../../…` back to the
repo root.
