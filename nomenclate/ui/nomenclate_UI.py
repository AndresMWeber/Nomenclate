from PyQt5 import QtCore, QtGui, QtWidgets

QtWidgets.QApplication.setApplicationName('progname')
QtWidgets.QApplication.setApplicationVersion('0.1')

name = QtGui.qApp.applicationName()
version = QtGui.qApp.applicationVersion()
