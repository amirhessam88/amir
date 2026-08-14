# 📦 rag-core

Shared RAG primitives for the amir monorepo.

- 📄 PDF ingest via LlamaIndex or LangChain (same pypdf loader)
- 🧮 Local embeddings (`BAAI/bge-small-en-v1.5`)
- 🗄️ Persistent Chroma per strategy under `.data/indexes/`
- 💬 OpenAI-backed query + citations

```python
from rag.core import RagConfig, ingest_papers, ask

config = RagConfig.from_env()
ingest_papers(config=config)
result = ask(question="What is driver node control?", config=config)
print(result.answer)
print(result.citations_markdown)
```

Docs: `/rag-core/` ·
[RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html).
