from importlib import import_module
import sys
from six import iteritems
import Qt.QtWidgets as QtWidgets
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO


class Platform(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    APPLICATIONS = {'maya':
                        {'basename': 'maya',
                         'mixin': 'maya.app.general.mayaMixin.MayaQWidgetDockableMixin',#MayaQDockWidget',
                         'imports': ['maya', 'maya.cmds', 'maya.app.general.mayaMixin']},
                    'nuke':
                        {'basename': 'nuke',
                         'imports': ['nuke']},
                    'python':
                        {'basename': 'nomenclate',
                         'imports': ['os']}
                    }
    APPLICATIONS['nomenclate'] = APPLICATIONS['python'].copy()

    ACTIONS = {
        'rename':
            {'maya': lambda node, new_name: cmds.rename(file, new_name),
             'nuke': lambda node, new_name: nuke.Node(node)['name'].setValue(new_name),
             'python': lambda file, new_name: os.rename(file, os.path.join(os.path.dirname(file), new_name))
             }
    }

    def __init__(self):
        self.application = None
        self.env = None
        self.platform_mixin = None

        for action in self.ACTIONS:
            setattr(self, action, lambda: NotImplementedError)

        self.auto_populate_platform()

    def auto_populate_platform(self):
        self.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        #self.LOG.info('Active platform detected as: %s' % self.application.platform())
        self.env = self.get_environment()
        self.LOG.info('Active environment detected as: %s' % self.env)
        for module_string in self.get_platform_import():
            import_module(module_string)
            self.LOG.info('Imported module %s: %s' % (module_string, bool(sys.modules.get(module_string))))
        self.platform_mixin = self.populate_mixin()
        self.LOG.info('Default platform mixin is %s: %s' % (self.env, self.platform_mixin))
        self.populate_functions()

    def populate_mixin(self):
        mixin = self.APPLICATIONS.get(self.env).get('mixin', 'None')
        mixin_python_object = sys.modules.get(mixin.split('.')[0])
        for sub_part in mixin.split('.')[1:]:
            mixin_python_object = getattr(mixin_python_object, sub_part)
        return mixin_python_object

    def populate_functions(self):
        for method_name, platform_methods in iteritems(self.ACTIONS):
            setattr(self, method_name, platform_methods.get(self.env))
            self.LOG.info('Populating action %s with %s' % (method_name, platform_methods.get(self.env)))

    def get_environment(self):
        pyqt_application_name = self.application.applicationName()

        for application in list(self.APPLICATIONS):
            if application in pyqt_application_name.lower():
                return self.APPLICATIONS[application].get('basename', '')

        if self.application.applicationName() == '':
            self.application.setApplicationName('Nomenclate')

        return self.application.applicationName()

    def get_platform_import(self):
        return self.APPLICATIONS[self.env].get('imports', 'None')

current = Platform()