import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath("..")))
sys.path.insert(0, os.path.dirname(os.path.abspath("../citam")))

# -- Project information -----------------------------------------------------
project = "CITAM"
copyright = "2020, Corning Incorporated"
author = "Mardochee Reveil, Chris Soper, Amit Jha"

release = "0.9.0"
master_doc = "index"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

extensions = [
    "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.doctest",
    "sphinx.ext.inheritance_diagram",
    # 'sphinx.ext.autosectionlabel',
    "sphinx.ext.mathjax",
    "numpydoc",
    "sphinx.ext.viewcode",
    "sphinxarg.ext"
    # 'matplotlib.sphinxext.only_directives',
    # 'matplotlib.sphinxext.plot_directive',
    # 'matplotlib.sphinxext.ipython_directive',
    # 'matplotlib.sphinxext.ipython_console_highlighting'
]

# html_theme_options = {
#     'display_version': True,
#     'collapse_navigation': False,
#     'sticky_navigation': False,
#     'navigation_depth': 4,
#     'includehidden': False,
#     'titles_only': False,
# }

html_theme = "citam_theme"
html_theme_path = ["."]

# html_static_path = ['_static']
autoclass_content = "both"
autosummary_generate = True
autodoc_inherit_docstrings = True

autodoc_default_options = {
    "member-order": "bysource",
    "undoc-members": True,
    "private-members": True,
    "show-inheritence": True,
    "members": None,
}
autoapi_type = "python"
autoapi_dirs = ["../citam"]
