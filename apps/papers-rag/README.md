# 🚀 papers-rag

Streamlit chat UI over the papers Chroma index built by `papers-ingest`.

```bash
cp .env.example .env   # OPENAI_API_KEY=...
poe ingest-papers      # once (or after PDF changes)
poe run-papers-rag     # or: papers-rag
```

## ☁️ Streamlit Community Cloud

- Set secret `OPENAI_API_KEY` in the app dashboard.
- Pre-build or mount the Chroma directory (`.data/chroma/papers`) — see `docs/` for deploy notes.

Published docs: `/papers-rag/`.
