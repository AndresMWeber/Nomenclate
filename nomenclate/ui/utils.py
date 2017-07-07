from PyQt5 import QtGui, QtCore
import os

RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resource')
FONTS_PATH = os.path.join(RESOURCES_PATH, 'fonts')
ALPHANUMERIC_VALIDATOR = QtGui.QRegExpValidator(QtCore.QRegExp('[A-Za-z0-9_]*'))