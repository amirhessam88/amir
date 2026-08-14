# ☁️ Deploy

## 🐳 Docker

```bash
docker compose -f dockers/compose/local-rag.yml up --build
```

Mount `.data/indexes` so the container can read the pre-built indexes.
Pass `OPENAI_API_KEY` via env. Langflow uses a separate compose file
(`poe run-langflow`).

## 🎈 Streamlit Community Cloud

1. Point the Cloud app at `apps/papers-rag/src/papers_rag/app.py`.
2. Set secret `OPENAI_API_KEY`.
3. Mount or rebuild the Chroma directory — vectors live on disk.

This app is **deploy-code** (Streamlit + Docker), not a registered model
artifact. Serving modes and traffic strategies:
[MLOps Deployment Strategies](https://www.amirhessam.com/two-cents/mlops-deployment-strategies.html).

Product docs publish to GitHub Pages under `/papers-rag/` via `poe docs`.
