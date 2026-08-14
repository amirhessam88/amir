# 🏗️ buildtools

Build / workspace helpers for the monorepo.

| Script | Poe task | Role |
|--------|----------|------|
| `uv.py` | `poe sync` / `lock` / `upgrade` | Workspace install + dep upgrades |
| `docs.py` | `poe docs` | Landing hubs + Sphinx leaves → `site/` |
| `clean.py` | `poe clean` | Caches, coverage, build artifacts |

```bash
poe sync
poe lock
poe upgrade              # all packages
poe upgrade ruff mypy    # selected packages
poe docs
poe clean
```
