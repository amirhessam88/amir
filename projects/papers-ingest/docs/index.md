# 🧬 papers-ingest

CLI that builds the local Chroma index from `assets/pdf/papers`.

```{toctree}
:maxdepth: 2
:hidden:

pages/runbook
```

::::{grid} 1 1 1 1
:gutter: 2

:::{grid-item-card} ▶️ Runbook
:link: pages/runbook
:link-type: doc

Flags, rebuild vs append, and troubleshooting.
:::

::::

```mermaid
flowchart LR
  PDFs["assets/pdf/papers/*.pdf"] --> CLI["papers-ingest"]
  CLI --> Embed["bge-small local"]
  Embed --> Chroma[".data/chroma/papers"]
```
