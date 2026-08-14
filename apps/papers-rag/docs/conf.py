"""Sphinx config for papers-rag."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

project = "papers-rag"
copyright = "Amirhessam Tahmassebi"
author = "Amirhessam Tahmassebi"
release = "0.1.1"
version = release

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "autoapi.extension",
    "myst_parser",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 3
myst_fence_as_directive = ["mermaid"]
autoapi_dirs = [str(ROOT / "src")]
autoapi_add_toctree_entry = False
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]
autoapi_keep_files = False
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_use_ivar = True
napoleon_attr_annotations = False

templates_path: list[str] = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

html_theme = "furo"
html_title = "papers-rag"
html_static_path = ["_static"]
html_favicon = "../../../assets/img/logo_color_clear.png"
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
            "html": "💬",
            "class": "",
        },
    ],
}
