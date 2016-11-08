#!/usr/bin/env python
import os
import inspect
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
"""
    :module: toolbox
    :platform: N/A
    :synopsis: This module has random os functions that are useful
    :plans:
"""


def module_path(local_function):
    """
    returns the module path without the use of __file__.  Requires a function defined
    locally in the module.
    from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module
    """
    return os.path.abspath(inspect.getsourcefile(local_function))


def get_scripts_dir():
    return os.path.dirname(__file__)


def get_config_filepath():
    path = os.path.join(os.path.dirname(__file__), 'env.ini')
    return os.path.normpath(path.replace('\\\\','/'))