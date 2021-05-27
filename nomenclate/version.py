from os import path
from toml import load as toml_load

pyproject_path = path.abspath(path.join(path.dirname(__file__), "..", "pyproject.toml"))
__version__ = toml_load(pyproject_path)["tool"]["poetry"]["version"]

