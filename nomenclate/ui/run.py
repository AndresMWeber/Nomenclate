import sys

sys.path.append('C:\\Users\\andre\\Envs\\nomenclate\\Lib\\site-packages')
from PyQt5 import QtWidgets, QtCore
from main import MainDialog

MODULE_LOGGER_LEVEL_OVERRIDE = None

APPLICATIONS = ['Maya-2017', 'Maya-2016', 'Maya-2015', 'Nuke']
WINDOW_INSTANCE = None


def create():
    global WINDOW_INSTANCE

    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    if application.applicationName() == '':
        application.setApplicationName('Nomenclate')

    if WINDOW_INSTANCE is None:
        WINDOW_INSTANCE = MainDialog()
    WINDOW_INSTANCE.show()
    WINDOW_INSTANCE.raise_()

    if not application.applicationName() in APPLICATIONS:
        try:
            WINDOW_INSTANCE.LOG.info('Standalone-mode')
            sys.exit(application.exec_())
        except SystemExit:
            pass
    else:
        WINDOW_INSTANCE.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    WINDOW_INSTANCE.LOG.info('%s running on %s' % (application.applicationName(), application.platformName()))


def delete():
    global WINDOW_INSTANCE

    if WINDOW_INSTANCE is None:
        return

    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()
