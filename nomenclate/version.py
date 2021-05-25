from toml import load as toml_load


__version__ = toml_load("pyproject.toml")["tool"]["poetry"]["version"]

