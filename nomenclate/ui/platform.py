from six import iteritems
import sys
import Qt.QtWidgets as QtWidgets


class Platform(object):
    APPLICATIONS = {'maya': 'maya',
                    'nuke': 'nuke',
                    'nomenclate': 'nomenclate'}

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
        for action in self.ACTIONS:
            setattr(self, action, lambda: NotImplementedError)
        self.auto_populate_platform()

    def auto_populate_platform(self):
        self.application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        self.env = self.get_environment()
        self.populate_functions()

    def populate_functions(self):
        for method_name, platform_methods in iteritems(self.ACTIONS):
            setattr(self, method_name, platform_methods.get(self.env))

    def get_environment(self):
        pyqt_application_name = self.application.applicationName()

        for application in list(self.APPLICATIONS):
            if application in pyqt_application_name.lower():
                return self.APPLICATIONS[application]

        if self.application.applicationName() == '':
            self.application.setApplicationName('Nomenclate')

        return self.application.applicationName()

    def platform_import(self):
        environment = self.get_environment()
        environment_lo = environment.lower()
        if 'maya' in environment_lo:
            import maya.cmds as cmds
        elif 'nuke' in environment_lo:
            import nuke
        elif 'nomenclate' in environment_lo:
            import os
