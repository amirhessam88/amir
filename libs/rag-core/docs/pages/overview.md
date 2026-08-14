# 🧭 Overview

| Module | Responsibility |
|--------|----------------|
| `config` | Paths, chunking, model ids (`RagConfig.from_env`) |
| `catalog` | Paper list + corpus-vs-paper question routing |
| `ingest` | PDF load (pypdf per page) → chunk → embed → Chroma |
| `index` | Open persistent collection / `VectorStoreIndex` |
| `query` | OpenAI LLM + retrieval query engine |
| `citations` | Turn source nodes into UI-friendly citations |

## 🆓 Why these defaults?

- **Local embeddings** — no per-token embedding bill while learning.
- **Chroma on disk** — inspectable, no Docker required for v1.
- **OpenAI only for generation** — clear free/paid boundary.
