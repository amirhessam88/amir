# ▶️ Runbook

## 🛠️ Prerequisites

1. `uv sync --locked --all-groups`
2. `cp .env.example .env` and set `OPENAI_API_KEY`
3. `poe ingest-papers --strategy llamaindex` (and/or `--strategy langchain`)

## 🚀 Launch

```bash
poe run-papers-rag
```

Streamlit starts with `--server.fileWatcherType none` so HuggingFace
`transformers` lazy imports do not spam `ModuleNotFoundError: torchvision`.
Restart after code changes — auto-reload is off.

## 🔑 OpenAI key

Streamlit does not source `.zshrc`. It inherits exported variables from the
process that launched it.

| Source | Works |
|--------|-------|
| Repo-root `.env` (`OPENAI_API_KEY=...`) | Yes — loaded from the monorepo root even though Streamlit cwd is the app script dir |
| `export OPENAI_API_KEY=...` in the same terminal, then `poe run-papers-rag` | Yes |
| Assignment without `export`, or a key only set in another terminal | No |
| Streamlit Cloud `secrets.toml` / dashboard secret | Yes (deploy) |

Process env wins over `.env` (`override=False`).

## 🎛️ UI

| Control | Meaning |
|---------|---------|
| Strategy | LlamaIndex or LangChain (isolated `.data/indexes/{strategy}`; switching clears chat) |
| Similarity top-k | Chunks kept after overfetch (`× 3`) + prose filter (1–12) |
| Clear chat | Reset session messages |
| Sources | Citations expander, collapsed |

Sidebar also shows LLM id, embed model, Chroma path, and index ready/empty.

`ask()` routing
([RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html)):

- Corpus questions (*all papers*, *common theme*) → `catalog.json`
- Author questions (*who is the main author*, *who wrote*) → `catalog.json`
- Otherwise → vector retrieve

If the index is empty: `poe ingest-papers --strategy llamaindex` (or
`langchain`). Chart-axis or `/uni00` sources: rebuild, then restart Streamlit.
