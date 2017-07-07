import nomenclate.settings as settings
from PyQt5 import QtWidgets, QtCore
from main import MainDialog
import logging
import sys
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

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        WINDOW_INSTANCE.LOG._log.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    handler = logging.StreamHandler(stream=sys.stdout)
    WINDOW_INSTANCE.LOG._log.addHandler(handler)

    sys.excepthook = handle_exception

    WINDOW_INSTANCE.LOG.info('%s running on %s' % (application.applicationName(), application.platformName()))
    WINDOW_INSTANCE.show()
    WINDOW_INSTANCE.raise_()
    application.setActiveWindow(WINDOW_INSTANCE)
    environment_application = application.applicationName()

    if not environment_application in APPLICATIONS:
        WINDOW_INSTANCE.LOG.info('Nomenclate running in %s-mode' % environment_application)
        execution_result = application.exec_()
    else:
        application.mode = '%s' % application.applicationName()
        WINDOW_INSTANCE.LOG.info('Nomenclate running in %s-mode' % environment_application)
        WINDOW_INSTANCE.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    print(execution_result)

def delete():
    global WINDOW_INSTANCE

    if WINDOW_INSTANCE is None:
        return

    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()