# ▶️ Runbook

```bash
uv sync --locked --all-groups
poe ingest-papers
```

Equivalent: `papers-ingest --rebuild`.

## 🎛️ Flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--rebuild / --no-rebuild` | rebuild | Wipe collection before writing |
| `--papers-dir` | `assets/pdf/papers` | PDF source directory |
| `--chroma-dir` | `.data/indexes/<strategy>` | Chroma persistence path |
| `--strategy` | `llamaindex` | `llamaindex`, `langchain`, or `all` |

Listing is non-recursive (`*.pdf` only). Both strategies share pypdf +
`is_prose_text` and write separate Chroma dirs. `--strategy all` cannot take
`--chroma-dir`.

Ingest writes `catalog.json` beside that strategy’s Chroma dir (filename +
220-character opening-page snippet). Pipeline:
[RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html).

## 🧯 Troubleshooting

- **No PDFs found** — files under `assets/pdf/papers/*.pdf` (not nested folders).
- **No extractable text** — image-only scans; pypdf needs text PDFs.
- **Slow first run** — embedding weights download once from HuggingFace.
- **Figure junk in sources** — rebuild after the prose filter, then restart
  Streamlit.
- **Stale corpus / author answers** — re-ingest to refresh `catalog.json`.
- **Mixed LlamaIndex / LangChain hits** — do not point both at one `CHROMA_DIR`.
