# 🛠️ devtools

Day-to-day engineer loop entrypoints. Root `poe` tasks call these scripts.

| Script | Poe task | Role |
|--------|----------|------|
| `greet.py` | `poe greet` | Welcome banner |
| `ruff.py` | `poe format` / check | Format + lint |
| `mypy.py` | `poe mypy` | Static types |
| `test.py` | `poe test` | Pytest + 100% coverage gate |
| `langflow.py` | `poe run-langflow` | Isolated Langflow studio (`uv tool run`) |

```bash
poe format   # ruff format + ruff check --fix (imports)
poe check    # greet + ruff format --check + ruff check + mypy
poe test
poe verify   # check + test
```
