# 🐳 dockers

Shared container assets for the monorepo.

| Path | Role |
|------|------|
| `bases/python-runtime/` | Slim Python org base |
| `templates/streamlit-app/` | Papers RAG image template |
| `compose/local-rag.yml` | Papers RAG Streamlit stack |
| `compose/local-langflow.yml` | Optional Langflow Docker (prefer `poe run-langflow`) |

Leaves should `FROM` these bases / templates rather than inventing snowflake Dockerfiles.
Shared bases live next to the code they provision:
[Building an Org Monorepo](https://www.amirhessam.com/two-cents/building-an-org-monorepo.html).
