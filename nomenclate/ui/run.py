import sys
from Qt import QtWidgets, QtCore
from nomenclate.ui.main import MainDialog
import nomenclate.ui.platform as platform_mod

SUPPORTED_APPLICATIONS = ['Maya-2017', 'Maya-2016', 'Maya-2015', 'Nuke']
WINDOW_INSTANCE = None


def create():
    global WINDOW_INSTANCE
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)

    platform = platform_mod.current
    if WINDOW_INSTANCE is None:
        WINDOW_INSTANCE = MainDialog()

    WINDOW_INSTANCE.LOG.info('%s running on %s' % (platform.env, platform.application.platformName()))
    application.setActiveWindow(WINDOW_INSTANCE)

    if platform.env in [app.lower() for app in list(SUPPORTED_APPLICATIONS)]:
        WINDOW_INSTANCE.LOG.info('Nomenclate running as a tool in %s-mode' % platform.env)
        WINDOW_INSTANCE.show(dockable=1, area='left')
        WINDOW_INSTANCE.raise_()
    else:
        WINDOW_INSTANCE.LOG.info('Nomenclate running standalone in %s-mode' % platform.env)
        WINDOW_INSTANCE.show()
        WINDOW_INSTANCE.raise_()
        application.exec_()

def delete():
    global WINDOW_INSTANCE

    if WINDOW_INSTANCE is None:
        return

    WINDOW_INSTANCE.deleteLater()
    WINDOW_INSTANCE = None


if __name__ == '__main__':
    create()
