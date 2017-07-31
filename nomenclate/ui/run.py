import sys
from Qt import QtWidgets, QtCore
import nomenclate.settings as settings
from nomenclate.ui.main import MainDialog
from nomenclate.ui.platform import Platform

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO

SUPPORTED_APPLICATIONS = ['Maya-2017', 'Maya-2016', 'Maya-2015', 'Nuke']
WINDOW_INSTANCE = None


def create():
    global WINDOW_INSTANCE
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    platform = Platform()

    if WINDOW_INSTANCE is None:
        WINDOW_INSTANCE = MainDialog()

    WINDOW_INSTANCE.LOG.info('%s running on %s' % (platform.env, platform.application.platformName()))
    WINDOW_INSTANCE.show()
    WINDOW_INSTANCE.raise_()
    application.setActiveWindow(WINDOW_INSTANCE)

    if not platform.env in SUPPORTED_APPLICATIONS:
        WINDOW_INSTANCE.LOG.info('Nomenclate running in %s-mode' % platform.env)
        application.exec_()
    else:
        WINDOW_INSTANCE.LOG.info('Nomenclate running as a tool in %s-mode' % platform.env)
        WINDOW_INSTANCE.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        WINDOW_INSTANCE.setWindowFlags(QtCore.Qt.Tool)

def delete():
    global WINDOW_INSTANCE

    if WINDOW_INSTANCE is None:
        return

    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()
