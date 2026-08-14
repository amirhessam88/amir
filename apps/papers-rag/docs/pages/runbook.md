# ▶️ Runbook

## 🛠️ Prerequisites

1. `uv sync --locked --all-groups`
2. `cp .env.example .env` and set `OPENAI_API_KEY`
3. `poe ingest-papers` (downloads the embedding model on first run)

## 🚀 Launch

```bash
poe run-papers-rag
```

Streamlit starts with `--server.fileWatcherType none`. That stops HuggingFace
`transformers` lazy imports from spamming `ModuleNotFoundError: torchvision`
(the watcher probes vision processors; this app only uses local text embeddings).
Restart the process after code changes — auto-reload is off.

## 🔑 OpenAI key

Streamlit does **not** source `.zshrc`. It inherits **exported** variables from
the process that launched it.

| Source | Works? |
|--------|--------|
| Repo-root `.env` (`OPENAI_API_KEY=...`) | Yes — loaded from the monorepo root even though Streamlit cwd is the app script dir |
| `export OPENAI_API_KEY=...` in the **same** terminal, then `poe run-papers-rag` | Yes |
| Assignment without `export`, or a key only set in another terminal | No |
| Streamlit Cloud `secrets.toml` / dashboard secret | Yes (deploy) |

Process env wins over `.env` (`override=False`).

## 🎛️ UI

| Control | Meaning |
|---------|---------|
| Similarity top-k | How many chunks to retrieve |
| Clear chat | Reset session messages |
| Sources expander | Citations with file / page / snippet |

Corpus questions (*all papers*, *common theme*) use the paper catalog, not
top-k chunks. Restart Streamlit after pulling this change.

If the index is empty, the app shows a clear error pointing at `poe ingest-papers`.
If sources look like chart axes or glyph salad, rebuild (`poe ingest-papers`)
and restart — figure pages are skipped by the prose filter.
