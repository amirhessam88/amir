<h1 align="center"><em>amir</em>: My AI Portfolio</h1>

<p align="center">
  <img src="assets/img/logo_color_clear.png" alt="amir" width="128" />
</p>

<p align="center">
  <strong>Production systems I shipped — rebuilt lean, still the real stack.</strong>
</p>

<p align="center">
  <a href="https://github.com/amirhessam88/amir/actions/workflows/ci.yml"><img alt="ci" src="https://github.com/amirhessam88/amir/actions/workflows/ci.yml/badge.svg" /></a>
  <a href="https://github.com/amirhessam88/amir/actions/workflows/docs.yml"><img alt="docs" src="https://github.com/amirhessam88/amir/actions/workflows/docs.yml/badge.svg" /></a>
  <a href="https://codecov.io/gh/amirhessam88/amir"><img alt="codecov" src="https://codecov.io/gh/amirhessam88/amir/graph/badge.svg?token=BAZKDIK929" /></a>
  <a href="https://pypi.org/project/amir/"><img alt="PyPI" src="https://img.shields.io/pypi/v/amir.svg" /></a>
  <a href="https://www.python.org/downloads/"><img alt="Python 3.11–3.13" src="https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white" /></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green.svg" /></a>
  <a href="https://amirhessam88.github.io/amir/"><img alt="Docs site" src="https://img.shields.io/badge/docs-GitHub%20Pages-3d9b6a" /></a>
</p>

AI portfolio monorepo: shared libs, Streamlit apps, ingest jobs, and a docs super-app. An open-source-first RAG stack over my research papers, with `uv` workspaces and an enforceable import DAG — the same shapes I shipped in production, smaller so you can see the wiring.

## ✨ What’s inside

| Path                                                | Product                                            | Docs                                                                |
| --------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------- |
| [`libs/rag-core`](libs/rag-core/)                   | LlamaIndex + Chroma + local embeddings + citations | [rag-core](https://amirhessam88.github.io/amir/rag-core/)           |
| [`projects/papers-ingest`](projects/papers-ingest/) | PDF → vector index CLI                             | [papers-ingest](https://amirhessam88.github.io/amir/papers-ingest/) |
| [`apps/papers-rag`](apps/papers-rag/)               | Streamlit query chat                               | [papers-rag](https://amirhessam88.github.io/amir/papers-rag/)       |

```mermaid
flowchart LR
  PDFs["assets/pdf/papers"] --> Ingest["papers-ingest"]
  Ingest --> Chroma["Chroma local"]
  Chroma --> App["papers-rag Streamlit"]
  App --> OpenAI["OpenAI GPT"]
  Embed["bge-small local"] --> Ingest
  Embed --> App
  Core["libs/rag-core"] --> Ingest
  Core --> App
```

Topology is strict: `apps/` and `projects/` may depend on `libs/` only. Full DAG and ADRs live in the [architecture portal](https://amirhessam88.github.io/amir/architecture/).

## 🚀 Quick start

```bash
uv tool install poethepoet
poe sync                      # install workspace from uv.lock
cp .env.example .env          # set OPENAI_API_KEY
poe ingest-papers             # first run downloads the embedding model
poe run-papers-rag            # open the Streamlit chat
poe docs                      # build the docs super-app into site/
```

Then open `site/index.html` — or the published hub at [amirhessam88.github.io/amir](https://amirhessam88.github.io/amir/).

## 📦 PyPI

```bash
pip install amir
```

One wheel. It bundles `rag.core`, `papers_rag`, and `papers_ingest` (APIs plus the `papers-ingest` / `papers-rag` CLIs). Not a git checkout: no docs portal, no `poe` toolchain, no paper PDFs. Leaf dirs stay workspace packages locally; they are not published on their own.

```bash
export OPENAI_API_KEY=...
export PAPERS_DIR=/path/to/pdfs
export CHROMA_DIR=/path/to/chroma
papers-ingest
papers-rag
```

Clone this repo when you want the full org (docs, PDFs, Docker, developer loop).

## 🆓 Free / OSS stack

| Layer         | Choice                           | Cost     |
| ------------- | -------------------------------- | -------- |
| Orchestration | LlamaIndex                       | OSS      |
| Embeddings    | `BAAI/bge-small-en-v1.5` (local) | Free     |
| Vector DB     | Chroma (persistent dir)          | Free     |
| LLM chat      | OpenAI API                       | Your key |
| Docs hosting  | GitHub Pages                     | Free     |

## 🧪 Quality

`poe test` gates **100%** branch coverage on `amir`, `rag.core`, `papers_rag`, and `papers_ingest`. CI runs that suite on Ubuntu and macOS across Python 3.11–3.13, then uploads `xmlcov/coverage.xml` to [Codecov](https://codecov.io/gh/amirhessam88/amir).

```bash
poe verify    # check (ruff + mypy) + test
```

Same gate CI runs. Dep upgrades: `poe upgrade` (or `poe upgrade ruff`). See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📚 Docs

| Hub           | URL                                                                  |
| ------------- | -------------------------------------------------------------------- |
| Landing       | [amirhessam88.github.io/amir](https://amirhessam88.github.io/amir/)  |
| Architecture  | […/architecture/](https://amirhessam88.github.io/amir/architecture/) |
| Local preview | `poe docs` → `site/index.html`                                       |
