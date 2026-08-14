# ☁️ Deploy notes

This monorepo intentionally supports **multiple deploy patterns**.

## 🐳 Docker (local / VPS)

```bash
docker compose -f dockers/compose/local-rag.yml up --build
```

Mount `.data/chroma/papers` so the container can read the pre-built index.
Pass `OPENAI_API_KEY` via env.

## 🎈 Streamlit Community Cloud

1. Point the Cloud app at `apps/papers-rag/src/papers_rag/app.py`.
2. Set secret `OPENAI_API_KEY`.
3. Either commit a small demo index (usually **not** recommended) or run ingest
   in a bootstrap step / persistent volume — Chroma needs the vectors on disk.

## 📄 Docs

Product docs publish to GitHub Pages under `/papers-rag/` via `poe docs`.
