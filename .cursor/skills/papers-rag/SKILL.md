---
name: papers-rag
description: Ingest, query, and debug the Papers RAG product (LlamaIndex + Chroma + Streamlit).
---

# Papers RAG

## Happy path

```bash
cp .env.example .env   # OPENAI_API_KEY
poe ingest-papers
poe run-papers-rag
```

## Debug

- Empty index → `IndexMissingError` → run ingest.
- Missing key → `OSError` from `require_openai_api_key`. Streamlit does not
  source `.zshrc`; use repo-root `.env` or `export OPENAI_API_KEY` in the same
  terminal. Streamlit cwd is the script dir, so `load_repo_dotenv()` loads the
  monorepo `.env` explicitly.
- `ModuleNotFoundError: torchvision` spam → Streamlit file watcher probing
  HuggingFace vision modules. `poe run-papers-rag` sets
  `--server.fileWatcherType none`. Do not add torchvision.
- Bad retrieval → tune `SIMILARITY_TOP_K`, chunk size, or rebuild index.
- Garbled / binary source snippets → old UTF-8 PDF decode; rebuild index.
- Chart-axis / pyLDAvis junk in sources → figure pages. Rebuild after the
  prose filter (`poe ingest-papers`), then restart Streamlit.
- “Both papers” / one-paper answer to “all papers” → need corpus routing.
  Restart Streamlit. Optional: `poe ingest-papers` to refresh `catalog.json`.

## Code map

- Core: `libs/rag-core/src/rag/core/` (`catalog.py` for corpus questions)
- Ingest CLI: `projects/papers-ingest/`
- Streamlit: `apps/papers-rag/src/papers_rag/app.py`
