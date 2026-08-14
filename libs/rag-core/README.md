# 📦 rag-core

Shared RAG primitives for the amir monorepo.

- 📄 PDF ingest via LlamaIndex
- 🧮 Local embeddings (`BAAI/bge-small-en-v1.5`)
- 🗄️ Persistent Chroma vector store
- 💬 OpenAI-backed query engine + citations

```bash
from rag.core import RagConfig, ingest_papers, ask

config = RagConfig.from_env()
ingest_papers(config=config)
result = ask(question="What is driver node control?", config=config)
print(result.answer)
print(result.citations_markdown)
```

See the Sphinx docs under `docs/` (published at `/rag-core/`).
