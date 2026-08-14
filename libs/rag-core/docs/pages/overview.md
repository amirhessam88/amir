# 🧭 Overview

`rag.core` is the shared Papers RAG library. Apps and ingest CLIs import it;
`libs/` does not import `apps/` or `projects/`.

Pipeline: pypdf pages → overlap chunks → local `bge-small` embeddings → Chroma
→ OpenAI. A prose filter and catalog routing (corpus / author questions skip
vector search) sit on that path.

See [RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html)
for cue lists, prompts, and the env table.

## 📦 Modules

| Module | Responsibility |
|--------|----------------|
| `strategy` | `RagStrategy` (`llamaindex` / `langchain`) + `.data/indexes/{strategy}` |
| `config` | `RagConfig.from_env` — paths, models, chunking, top-k |
| `loaders` | Non-recursive `*.pdf`; pypdf page extraction + prose skip |
| `text_quality` | `is_prose_text` (ingest and query) |
| `passage` | Author cues, acknowledgement / SPIE filters, page labels, `QA_GROUNDING_RULES` |
| `catalog` | `catalog.json` + `QueryScope` (paper vs corpus) |
| `ingest` | Dispatch + LlamaIndex chunk → embed → Chroma |
| `index` | Open persistent LlamaIndex collection; `IndexMissingError` |
| `query` | `ask()` routing, LlamaIndex engine, catalog synthesis |
| `citations` | `Citation` (`file_name`, `page`, `score`, `snippet`) |
| `backends` | `RagBackend` protocol; LlamaIndex and LangChain |

Public API: `RagConfig`, `RagStrategy`, `ingest_papers`, `ask`,
`build_query_engine`, `Citation`, `QueryResult`, `IndexMissingError`.

## 🎛️ Strategies

Do not share one Chroma folder across backends.

| Strategy | Splitter | Query path | Default persist |
|----------|----------|------------|-----------------|
| `llamaindex` | `SentenceSplitter` | Query engine + `ProseNodePostprocessor` | `.data/indexes/llamaindex/` |
| `langchain` | `RecursiveCharacterTextSplitter` | Retriever → labeled context → `ChatOpenAI` | `.data/indexes/langchain/` |

Shared: pypdf loader, `is_prose_text`, `chunk_size=1024` / `overlap=128`,
`BAAI/bge-small-en-v1.5`, collection name `papers`, overfetch `top_k × 3`.

`CHROMA_DIR` overrides persist for one strategy. `--strategy all` cannot take
`--chroma-dir`.

## 🧭 `ask()` routing

1. **Author cues** (`who wrote`, `main author`, `authors of`, … — not bare
   `"author"`) → `catalog.json` + `AUTHOR_SYNTHESIS_PROMPT`.
2. **Corpus cues** (`all papers`, `common theme`, …) → catalog +
   `CORPUS_SYNTHESIS_PROMPT`.
3. **Otherwise** → vector retrieve, drop non-prose, generate with
   `QA_GROUNDING_RULES`.

Ingest writes `catalog.json` beside each strategy’s Chroma dir (filename +
220-char opening snippet). Missing JSON falls back to `papers_dir` filenames.

## ⚙️ Environment

| Variable | Default |
|----------|---------|
| `OPENAI_API_KEY` | required for chat |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `EMBED_MODEL` | `BAAI/bge-small-en-v1.5` |
| `RAG_STRATEGY` | `llamaindex` |
| `PAPERS_DIR` | `assets/pdf/papers` |
| `CHROMA_DIR` | `.data/indexes/{strategy}` |
| `CHROMA_COLLECTION` | `papers` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1024` / `128` |
| `SIMILARITY_TOP_K` | `5` |

`load_repo_dotenv()` loads cwd `.env` then repo-root `.env`. Process env wins
(`override=False`).

## 🆓 Defaults

- Local embeddings — no embedding API bill.
- Chroma on disk — no Docker for the local loop.
- OpenAI only for generation.
- Isolated strategy dirs so LlamaIndex and LangChain collections stay separate.
