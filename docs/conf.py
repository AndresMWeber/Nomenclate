# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(".."))


# -- Project information -----------------------------------------------------

project = "nomenclate"
copyright = "2017, Andres Weber <andres.weber.dev@gmail.com>"
author = "Andres Weber <andres.weber.dev@gmail.com>"

# The full version, including alpha/beta/rc tags
from nomenclate import __version__

release = __version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.autosummary",
]
templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".tox"]
html_theme = "alabaster"
html_static_path = []
pygments_style = "sphinx"
todo_include_todos = True

on_rtd = os.environ.get("READTHEDOCS", None) == "True"
if not on_rtd:  # only import and set the theme if we're building docs locally
    try:
        import sphinx_rtd_theme
    except ImportError:
        html_theme = "default"
        html_theme_path = []
    else:
        html_theme = "sphinx_rtd_theme"
        html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

doctest_global_setup = "import nomenclate"
