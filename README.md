<h1 align="center"><em>amir</em>: My AI Portfolio</h1>

<p align="center">
  <img src="https://raw.githubusercontent.com/amirhessam88/amir/master/assets/img/logo_color_clear.png" alt="amir" width="128" />
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

An **org monorepo** for AI products: shared libraries, apps, batch jobs, and a
docs hub. `apps/` and `projects/` depend on `libs/` only. The first product is a
papers RAG stack — runbooks, APIs, and architecture live in the docs.

## 📚 Docs

**[amirhessam88.github.io/amir](https://amirhessam88.github.io/amir/)** is the
front door (topology cards → each product). Locally: `poe docs` → `site/index.html`.

| Place | Where |
| ----- | ----- |
| Architecture | [topology](https://amirhessam88.github.io/amir/architecture/), [RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html), [toolchain](https://amirhessam88.github.io/amir/architecture/toolchain.html) |
| Products | [rag-core](https://amirhessam88.github.io/amir/rag-core/), [papers-rag](https://amirhessam88.github.io/amir/papers-rag/), [papers-ingest](https://amirhessam88.github.io/amir/papers-ingest/) |
| Contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |

## 🗺️ Layout

| Path | Role |
| ---- | ---- |
| `apps/` | User-facing UIs and CLIs |
| `libs/` | Shared packages (kebab distro → nested import) |
| `projects/` | Domain jobs and ingest CLIs |
| `services/` | Reserved for network services |
| `tools/` | `poe` tasks and shared configs |
| `dockers/` | Base images and compose |
| `docs/` | Landing hub + architecture portal |

## 🚀 Local loop

```bash
uv tool install poethepoet
poe sync      # install the workspace from uv.lock
poe verify    # ruff + mypy + tests
poe docs      # build the docs super-app into site/
```

Product runbooks are in the docs linked above. Clone this repo for PDFs,
Docker, and the developer loop.

## 📦 PyPI

```bash
pip install amir
```

One wheel; leaf packages are not published on their own. Env vars and CLIs:
[toolchain](https://amirhessam88.github.io/amir/architecture/toolchain.html).
