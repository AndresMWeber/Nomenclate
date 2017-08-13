import Qt.QtWidgets as QtWidgets
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO


class DefaultPlatform(object):
    DOCKABLE_APPLICATIONS = ['Maya-2017', 'Maya-2016', 'Maya-2015', 'Nuke']
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    BASENAME = None
    DOCKABLE = False
    RUN_KWARGS = {}
    PLATFORM_MIXIN = None

    def __init__(self):
        self.application = None
        self.env = None
        self.platform_mixin = None
        self.auto_populate_platform()

    def auto_populate_platform(self):
        self.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        self.env = self.get_environment()
        self.LOG.info('Loaded environment %s modules imported with default platform mixin: %s' % (self.env,
                                                                                                  self.platform_mixin))

    def get_environment(self):
        if self.application.applicationName() == '':
            self.application.setApplicationName('python')
        return self.application.applicationName()

    def show(self, window_instance):
        self.LOG.info(
            '%s running on %s with instance %s' % (self.env, self.application.platformName(), window_instance))
        if self.DOCKABLE:
            self.LOG.info('Nomenclate running as a tool in %s-mode, starting docked...' % self.env)
            window_instance.show(**self.RUN_KWARGS)
            window_instance.raise_()
        else:
            self.LOG.info('Nomenclate running standalone in %s-mode' % self.env)
            window_instance.show()
            window_instance.raise_()
            self.application.setActiveWindow(window_instance)
            self.application.exec_()

    @classmethod
    def rename(cls, node_path, new_name, keep_extension=True):
        raise NotImplementedError

    @classmethod
    def exists(cls, node_path):
        raise NotImplementedError

    @classmethod
    def close(cls, ui):
        ui.deleteLater()
