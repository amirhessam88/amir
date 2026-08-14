# 🚀 papers-rag

Streamlit chat UI over the papers Chroma index built by `papers-ingest`.

```bash
cp .env.example .env   # OPENAI_API_KEY=...
poe ingest-papers --strategy llamaindex
poe ingest-papers --strategy langchain
poe run-papers-rag     # or: papers-rag
```

Pick the strategy in the Streamlit sidebar. Each backend has its own persist dir
under `.data/indexes/`.

## ☁️ Streamlit Community Cloud

- Set secret `OPENAI_API_KEY` in the app dashboard.
- Pre-build or mount the Chroma directory (`.data/indexes/llamaindex`). See `docs/` for deploy.

Published docs: `/papers-rag/`.
[RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html).
