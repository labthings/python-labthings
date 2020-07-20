project = "Python-LabThings"
copyright = "2020, Joel Collins"
author = "Joel Collins"


extensions = [
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "autoapi.extension",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

master_doc = "index"

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autoapi_dirs = ["../src/labthings"]
autoapi_ignore = [
    "*/server/*",
    "*/core/*",
]

autoapi_generate_api_docs = False

intersphinx_mapping = {
    "marshmallow": ("https://marshmallow.readthedocs.io/en/stable/", None),
    "webargs": ("https://webargs.readthedocs.io/en/latest/", None),
    "apispec": ("https://apispec.readthedocs.io/en/latest/", None),
    "flask": ("https://flask.palletsprojects.com/en/1.1.x/", None),
}
