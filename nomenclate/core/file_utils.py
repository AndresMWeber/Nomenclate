import os
import yaml
from shutil import copy
from typing import List, Callable
from pathlib import Path
from .errors import SourceError


def find_file(search_paths: List[str], validator: Callable = None) -> str:
    """ Validates the filepath to the config.  

    :param filename: str, file path to the config file to query
    :param validator: func, a function that validates the file in question by throwing an error if it is invalid.
    :raises: IOError, OSError
    """
    for search_path in search_paths:
        if validator:
            try:
                validator(search_path)
                return search_path
            except (IOError, OSError):
                pass

    raise SourceError("No config file found or it is not a valid YAML file")


def search_relative_cwd_user_dirs_for_file(filename: str = "", validator: Callable = None) -> str:
    """ Validates the filepath to the config.
        Searches:
            - relative file path (./{config_filename})
            - ~/{config_filename}
            - os.cwd()/{config_filename}
            - configuratior.py.__path__/{config_filename}

    :param filename: str, file path to the config file to query
    :param validator: func, a function that validates the file in question by throwing an error if it is invalid.
    :raises: IOError, OSError
    """
    search_paths = [
        filename,
        os.path.normpath(os.path.join(str(Path.home()), filename)),
        os.path.normpath(os.path.join(os.getcwd(), filename)),
        os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)),
    ]
    return find_file(search_paths, validator=validator)


def validate_yaml_file(file_path: str) -> None:
    """ Validates the filepath to the config.  Detects whether it is a true YAML file + existance

    :param file_path: str, file path to the config file to query
    :raises: IOError
    """

    is_file = os.path.isfile(file_path)
    if not is_file and os.path.isabs(file_path):
        raise IOError(
            "File path %s is not a valid yml, ini or cfg file or does not exist" % file_path
        )

    elif is_file:
        if os.path.getsize(file_path) == 0:
            raise IOError("File %s is empty" % file_path)

    with open(file_path, "r") as f:
        if yaml.safe_load(f) is None:
            raise IOError("No YAML config was found in file %s" % file_path)


def copy_file_to_home_dir(file_path: str, copy_filename: str):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    return copy(file_path, str(Path.home() / copy_filename))
