# 🤝 Contributing to amir

Thanks for helping keep this monorepo healthy. Humans and agents follow the same loop.

## 🧰 Toolchain

| Tool | Role |
|------|------|
| **uv** | Workspace installs + lockfile |
| **poethepoet** | Task runner (`poe …`) |
| **ruff** | Format + lint |
| **mypy** | Static types |
| **pytest** + **assertpy** | Tests |
| **tox** + **tox-uv** | Multi-Python matrix |
| **Sphinx** + **Furo** | Per-product docs |

```bash
uv tool install poethepoet
poe sync                 # uv workspace → .venv (all groups + packages)
cp .env.example .env     # add OPENAI_API_KEY for chat
poe verify               # check + test
poe docs
```

Useful monorepo tasks: `poe sync`, `poe lock`, `poe upgrade` (all or named packages),
`poe verify`, `poe test`, `poe docs`. See `tools/README.md`.

## 📁 Topology contracts

- `apps/*`, `projects/*`, `services/*` may depend on `libs/*` only.
- Libs never import apps/projects/services.
- Distro name is kebab-case (`rag-core`); import path replaces `-` with `.` (`rag.core`).
- Every product leaf ships a Sphinx `docs/` node and a card on `docs/landing/`.

## ✍️ Style

- Prefer **named keyword arguments** at call sites (`ask(question=q, config=cfg)`).
- Use **numpydoc** for all Python docstrings (not Google / free-form).
- Prefer **`Enum` / `StrEnum` / `IntEnum`** over magic strings/ints for closed sets of values.
- Add **comments only when needed** (non-obvious why); rely on clear names + numpydoc otherwise.
- See `.cursor/rules/named-arguments.mdc`, `.cursor/rules/numpydoc.mdc`,
  `.cursor/rules/enums.mdc`, and `.cursor/rules/comments.mdc`.

## 🧪 Tests

- Unit tests live under each leaf’s `tests/unit/`.
- Use **assertpy** (`assert_that(...)`), not bare `assert`.
- Markers: `slow`, `needs_openai`, `needs_embed`, `integration` — default `poe test` skips the heavy ones.
- **100%** coverage required on `amir`, `rag.core`, `papers_rag`, and `papers_ingest` (`poe test` enforces it).
- CI uploads `xmlcov/coverage.xml` to [Codecov](https://codecov.io/gh/amirhessam88/amir) from the Ubuntu / Python 3.12 job.

## 🔐 Secrets

- Never commit API keys. Use `.env` (gitignored) from `.env.example`.
- Streamlit Cloud uses secrets.toml / dashboard secrets — documented in app docs.

## 📚 Docs

```bash
poe docs   # writes site/ (landing + /rag-core/ + /papers-rag/ + /papers-ingest/ + /architecture/)
```

Narrative docs use emoji wayfinding and Mermaid diagrams. See `.cursor/rules/docs-and-emoji.mdc`.
