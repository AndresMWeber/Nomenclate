import PyQt5.QtWidgets as QtWidgets


class Default(object):
    TITLE = 'Default Widget'
    TOP = 10
    LEFT = 10
    WIDTH = 640
    HEIGHT = 480

    def __init__(self):
        super(Default, self).__init__()
        self.title = self.TITLE
        self.setup()

    def setup(self):
        self.create_controls()
        self.initialize_controls()
        self.connect_controls()

    def create_controls(self):
        raise NotImplementedError

    def initialize_controls(self):
        raise NotImplementedError

    def connect_controls(self):
        raise NotImplementedError

    def closeEvent(self, event):
        print("widget closing %s" % self)
        super(Default, self).closeEvent(event)

class DefaultWidget(QtWidgets.QWidget, Default):
    pass


class DefaultFrame(QtWidgets.QFrame, Default):
    pass


class DefaultDialog(QtWidgets.QDialog, Default):
    pass


class QCollapsableTree(QtWidgets.QTreeView):
    pass
