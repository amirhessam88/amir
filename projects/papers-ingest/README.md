# 🧬 papers-ingest

CLI that loads PDFs from `assets/pdf/papers`, chunks them, embeds with a local
HuggingFace model, and writes a persistent Chroma index under `.data/chroma/papers`.

```bash
poe ingest-papers
# or
papers-ingest --help
papers-ingest --no-rebuild
```

See `docs/` for the full runbook (published at `/papers-ingest/`).
