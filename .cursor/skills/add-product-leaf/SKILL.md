---
name: add-product-leaf
description: Checklist for hand-adding a new apps/libs/projects/services leaf in the amir monorepo (no Copier).
---

# Add a product leaf

1. Choose top-level: `apps/`, `libs/`, `projects/`, or `services/`.
2. Create kebab directory + `pyproject.toml` (workspace member).
3. For libs: `src/<slash-path>/` matching hyphen→nested map (`rag-core` → `rag/core`).
4. Add `tests/unit/`, `docs/` (Sphinx + Furo + emoji pages + AutoAPI for `src/`), `ci.yml`, README.
5. Wire path deps with `[tool.uv.sources]` → `{ workspace = true }`.
6. Add stub workflow under `.github/workflows/` calling `_python-leaf.yml`.
7. Add a card on the matching topology hub under `docs/landing/` and register the leaf in `tools/buildtools/docs.py`.
8. Run `poe lock && poe sync`, then `poe verify && poe docs`.
9. Never invent a new top-level directory outside the topology.
