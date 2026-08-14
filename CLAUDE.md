# amir — agent instructions

This is Amir's AI portfolio org monorepo. Follow the same contracts as humans:

- Tooling: `uv`, `poe`, `ruff`, `mypy`, `pytest`/`assertpy`, Sphinx.
- Topology: `apps|projects|services → libs` only; kebab distro → nested import (`rag-core` → `rag.core`).
- Style: named kwargs; numpydoc; Enums over magic literals; comments only when needed (see `.cursor/rules/`).
- Every product leaf needs Sphinx `docs/` + a `docs/landing` card.
- Secrets: never commit `.env` / API keys; use `.env.example`.
- Details: `.cursor/rules/*`, `docs/ai/*`, `CONTRIBUTING.md`.

Canonical local loop: `poe sync && poe verify && poe docs`.
