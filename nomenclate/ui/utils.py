from PyQt5 import QtGui, QtCore
import os

ALPHANUMERIC_VALIDATOR = QtCore.QRegExp('[A-Za-z0-9_]*')
TOKEN_VALUE_VALIDATOR = QtCore.QRegExp('^(?!^_)(?!.*__+|\.\.+.*)[a-zA-Z0-9_\.]+(?!_)$')
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resource')
FONTS_PATH = os.path.join(RESOURCES_PATH, 'fonts')