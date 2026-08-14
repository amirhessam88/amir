"""Sphinx config for papers-ingest."""

from __future__ import annotations

project = "papers-ingest"
copyright = "Amirhessam Tahmassebi"
author = "Amirhessam Tahmassebi"
release = "0.1.0"
version = release

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

html_theme = "furo"
html_title = "papers-ingest"
html_static_path = ["_static"]
html_favicon = "../../../docs/landing/img/logo_color_clear.png"
html_css_files = ["css/custom.css", "css/footer.css"]
html_show_sphinx = False
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#3d9b6a",
        "color-brand-content": "#2d7a52",
    },
    "dark_css_variables": {
        "color-brand-primary": "#c4a35a",
        "color-brand-content": "#c4a35a",
    },
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/amirhessam88/amir",
            "html": "🧬",
            "class": "",
        },
    ],
}
