import Qt.QtWidgets as QtWidgets
import nomenclate.settings as settings
from . import platform_registry as registry

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO

LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)


def platform_identifier(platform_name):
    identifiers = ['maya', 'nuke', 'houdini', 'python']
    for identifier in identifiers:
        if identifier in platform_name.lower():
            return identifier
    return platform_name or 'python'


def get_current_platform():
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app = platform_identifier(application.applicationName())
    LOG.info('current application: %s' % app)
    if 'maya' in app.lower():
        app = 'maya'
        LOG.info('importing maya plugin')
        import nomenclate.ui.platforms.p_maya

    elif 'nuke' in app.lower():
        LOG.info('importing nuke plugin')
        import nomenclate.ui.platforms.p_nuke

    elif 'python' in app.lower():
        LOG.info('importing os plugin')
        import nomenclate.ui.platforms.p_os

    return registry.REGISTERED_PLATFORMS.get(app, None)()
