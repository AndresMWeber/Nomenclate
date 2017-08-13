import Qt.QtWidgets as QtWidgets
import nomenclate.ui.platforms as platforms


class Default(object):
    TITLE = 'Default Widget'

    def __init__(self, parent=None, *args, **kwargs):
        super(Default, self).__init__(parent=parent, *args, **kwargs)
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


class DefaultNormalWindow(Default, QtWidgets.QWidget):
    pass


if platforms.current.PLATFORM_MIXIN:
    class DefaultMixinWindow(platforms.current.PLATFORM_MIXIN, DefaultNormalWindow):
        pass
else:
    DefaultMixinWindow = None

DefaultWindow = DefaultMixinWindow if platforms.current.PLATFORM_MIXIN else DefaultNormalWindow


class DefaultWidget(Default, QtWidgets.QWidget):
    pass


class DefaultFrame(Default, QtWidgets.QFrame):
    pass


class DefaultDialog(Default, QtWidgets.QDialog):
    pass


class QCollapsableTree(Default, QtWidgets.QTreeView):
    pass
