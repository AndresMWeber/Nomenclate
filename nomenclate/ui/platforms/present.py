import Qt.QtWidgets as QtWidgets
from . import platform_registry as registry


def platform_identifier(platform_name):
    identifiers = ['maya', 'nuke', 'houdini', 'python']
    for identifier in identifiers:
        if identifier in platform_name.lower():
            return identifier
    return platform_name or 'python'

def get_current_platform():
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app = platform_identifier(application.applicationName())
    print('current application: %s' % app)
    if 'maya' in app.lower():
        app = 'maya'
        print('importing maya plugin')
        import nomenclate.ui.platforms.p_maya

    elif 'nuke' in app.lower():
        print('importing nuke plugin')
        import nomenclate.ui.platforms.p_nuke

    elif 'python' in app.lower():
        print('importing os plugin')
        import nomenclate.ui.platforms.p_os

    return registry.REGISTERED_PLATFORMS.get(app, None)()
