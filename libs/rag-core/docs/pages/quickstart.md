# 🚀 Quick start

```python
from rag.core import RagConfig, ingest_papers, ask

config = RagConfig.from_env()
ingest_papers(config=config)  # rebuilds Chroma by default
result = ask(question="What is a driver node?", config=config)
print(result.answer)
print(result.citations_markdown)
```

Prefer the CLIs for day-to-day work:

```bash
poe ingest-papers
poe run-papers-rag
```
