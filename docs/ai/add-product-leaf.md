# 🌱 Add product leaf checklist

See also `.cursor/skills/add-product-leaf/SKILL.md` and
[Building an Org Monorepo](https://www.amirhessam.com/two-cents/building-an-org-monorepo.html).

1. Pick `apps/` | `libs/` | `projects/` | `services/`
2. `pyproject.toml` + src layout + workspace source
3. `tests/unit/` with assertpy
4. Sphinx `docs/` node
5. `ci.yml` + GitHub stub workflow
6. Topology hub card under `docs/landing/` + `tools/buildtools/docs.py` entry
7. `poe lock` · `poe sync` · `poe verify` · `poe docs`
