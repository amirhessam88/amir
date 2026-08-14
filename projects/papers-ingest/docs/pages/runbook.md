# ▶️ Ingest runbook

## 🚀 Happy path

```bash
uv sync --locked --all-groups
poe ingest-papers
```

Equivalent:

```bash
papers-ingest --rebuild
```

## 🎛️ Flags

| Flag | Default | Meaning |
|------|---------|---------|
| `--rebuild / --no-rebuild` | rebuild | Wipe collection before writing |
| `--papers-dir` | `assets/pdf/papers` | PDF source directory |
| `--chroma-dir` | `.data/chroma/papers` | Chroma persistence path |

## 🧯 Troubleshooting

- **No PDFs found** — confirm files live under `assets/pdf/papers/*.pdf`.
- **Slow first run** — the embedding model downloads once from HuggingFace.
- **Figure junk in sources** — chart/pyLDAvis pages. Rebuild after the prose
  filter, then restart Streamlit.
- **Corpus catalog** — ingest writes `catalog.json` beside Chroma for
  “all papers” questions.
