project = "Python-LabThings"
copyright = "2020, Joel Collins"
author = "Joel Collins"


extensions = [
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
