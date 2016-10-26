from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5 import QtCore, QtGui

QApplication.setApplicationName('progname')
QApplication.setApplicationVersion('0.1')

name = QtGui.qApp.applicationName()
version = QtGui.qApp.applicationVersion()
