# 🐳 dockers

Shared container assets for the monorepo.

| Path | Role |
|------|------|
| `bases/python-runtime/` | Slim Python org base |
| `templates/streamlit-app/` | Papers RAG image template |
| `compose/local-rag.yml` | Local compose stack |

Leaves should `FROM` these bases / templates rather than inventing snowflake Dockerfiles.
