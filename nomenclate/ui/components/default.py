import Qt.QtWidgets as QtWidgets
import nomenclate.ui.platform as platform



class Default(platform.current.platform_mixin or object):
    TITLE = 'Default Widget'

    def __init__(self, *args, **kwargs):
        super(Default, self).__init__(*args, **kwargs)
        self.category_label = self.TITLE
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
        super(Default, self).closeEvent(event)


class DefaultWindow(Default, QtWidgets.QWidget):
    pass

class DefaultWidget(Default, QtWidgets.QWidget):
    pass


class DefaultFrame(Default, QtWidgets.QFrame):
    pass


class DefaultDialog(Default, QtWidgets.QDialog):
    pass


class QCollapsableTree(Default, QtWidgets.QTreeView):
    pass
