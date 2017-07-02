import sys
import nomenclate.settings as settings
sys.path.append('C:\\Users\\Daemonecles\\Envs\\nomenclate\\Lib\\site-packages')
from PyQt5 import QtWidgets, QtCore
from main import MainDialog

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO

APPLICATIONS = ['Maya-2017', 'Maya-2016', 'Maya-2015', 'Nuke']
WINDOW_INSTANCE = None


def create():
    global WINDOW_INSTANCE

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    if application.applicationName() == '':
        application.setApplicationName('Nomenclate')

    if WINDOW_INSTANCE is None:
        WINDOW_INSTANCE = MainDialog()
    WINDOW_INSTANCE.LOG.setLevel(MODULE_LOGGER_LEVEL_OVERRIDE)
    WINDOW_INSTANCE.LOG.info('%s running on %s' % (application.applicationName(), application.platformName()))
    WINDOW_INSTANCE.show()
    WINDOW_INSTANCE.raise_()
    application.setActiveWindow(WINDOW_INSTANCE)
    environment_application = application.applicationName()
    if not environment_application in APPLICATIONS:
        try:
            WINDOW_INSTANCE.LOG.info('Nomenclate running in %s-mode' % environment_application)
            application.exec_()
        except SystemExit:
            WINDOW_INSTANCE.LOG.info('Nomenclate encountered an error trying to run')
            raise
    else:
        application.mode = '%s' % application.applicationName()
        WINDOW_INSTANCE.LOG.info('Nomenclate running in %s-mode' % environment_application)
        WINDOW_INSTANCE.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)


def delete():
    global WINDOW_INSTANCE

    if WINDOW_INSTANCE is None:
        return

    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()
