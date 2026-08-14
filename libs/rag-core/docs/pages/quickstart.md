# 🚀 Quick start

```python
from rag.core import RagConfig, ingest_papers, ask

config = RagConfig.from_env()
ingest_papers(config=config)  # rebuilds Chroma by default
result = ask(question="What is a driver node?", config=config)
print(result.answer)
print(result.citations_markdown)
```

`ask()` routes corpus and author questions through `catalog.json` before vector
search. Pipeline details:
[RAG stack](https://amirhessam88.github.io/amir/architecture/rag-stack.html).

```bash
poe ingest-papers --strategy llamaindex
poe ingest-papers --strategy langchain
```
