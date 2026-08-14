# 🗺️ Architecture

Monorepo topology, the papers RAG pipeline, and the developer toolchain. This
repo follows
[Building an Org Monorepo](https://www.amirhessam.com/two-cents/building-an-org-monorepo.html).

```{toctree}
:maxdepth: 2
:hidden:

overview
rag-stack
langflow
toolchain
```

::::{grid} 1 2 2 2
:gutter: 2

:::{grid-item-card} 📁 Topology
:link: overview
:link-type: doc

Directory contracts, import DAG, and product leaves.
:::

:::{grid-item-card} 🧠 RAG stack
:link: rag-stack
:link-type: doc

LlamaIndex + LangChain + Chroma + local embeddings + OpenAI chat.
:::

:::{grid-item-card} 🌊 Langflow
:link: langflow
:link-type: doc

Visual flow editor on port 7860.
:::

:::{grid-item-card} 🧰 Toolchain
:link: toolchain
:link-type: doc

uv · poe · ruff · mypy · tox · Sphinx.
:::

::::
