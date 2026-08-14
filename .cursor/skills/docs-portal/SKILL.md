---
name: docs-portal
description: Add Sphinx leaf docs and a landing card to the amir docs super-app.
---

# Docs portal

1. Create `docs/conf.py` + `docs/index.md` (+ pages) under the leaf.
2. Use Furo + MyST + mermaid; emoji section headers.
3. For product leaves with `src/`, enable sphinx-autoapi + napoleon (numpydoc)
   and add an API card pointing at `autoapi/<package>/index`.
4. Append `(docs_dir, site_name)` to `LEAVES` in `tools/buildtools/docs.py`.
5. Add a product card on the matching topology hub page under `docs/landing/`:
   - `apps/index.html` · `libs/index.html` · `projects/index.html` ·
     `services/index.html` · `tools/index.html` · `docs/index.html`
   - Use `href="../<site_name>/index.html"` (explicit `index.html` for `file://` preview).
   - Note: the `tools/` Sphinx handbook publishes to `site/toolbox/` so it does not
     collide with the `site/tools/` hub page.
6. Verify with `poe docs` and open `site/index.html` → topology card → product card.
