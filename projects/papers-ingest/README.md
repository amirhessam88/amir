# 🧬 papers-ingest

CLI that loads PDFs from `assets/pdf/papers`, chunks them, embeds with a local
HuggingFace model, and writes a persistent Chroma index under
`.data/indexes/<strategy>` (default LlamaIndex).

```bash
poe ingest-papers --strategy llamaindex
poe ingest-papers --strategy langchain
poe ingest-papers --strategy all
# or
papers-ingest --help
papers-ingest --strategy langchain --no-rebuild
```

See `docs/` (published at `/papers-ingest/`) and
[RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html).
