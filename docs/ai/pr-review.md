# 🕵️ PR review checklist (agents + humans)

- [ ] Import DAG respected (no leaf→leaf Python imports across apps/services)
- [ ] Lib naming: kebab distro ↔ nested import path
- [ ] New leaf has `docs/`, `ci.yml`, tests, and a landing card
- [ ] No secrets / `.env` committed
- [ ] Dockerfiles `FROM` shared `dockers/` bases when adding images
- [ ] `poe check` + `poe test` would pass
- [ ] Narrative docs use emoji + mermaid where architecture is explained
