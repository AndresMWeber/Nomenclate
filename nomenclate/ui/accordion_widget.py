import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from default import DefaultFrame, DefaultWidget
from six import iteritems


class QClickLabel(QtWidgets.QLabel):
    clicked = QtCore.pyqtSignal(QtWidgets.QLabel)
    def __init__(self, *args):
        super(QClickLabel, self).__init__(*args)

    def mousePressEvent(self, QMousePressEvent):
        self.clicked.emit(self)
        super(QClickLabel, self).mousePressEvent(QMousePressEvent)


class QAccordionCategory(DefaultFrame):
    def __init__(self, title, parent, *args, **kwargs):
        self.label_title = title
        self.parent = parent
        self.folded = False
        super(QAccordionCategory, self).__init__(*args, **kwargs)

    def create_controls(self):
        QtWidgets.QVBoxLayout(self)
        self.title = QClickLabel(self.label_title)
        self.fold_widget = QtWidgets.QFrame()
        QtWidgets.QVBoxLayout(self.fold_widget)

    def initialize_controls(self):
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)
        self.fold_widget.layout().setSpacing(2)
        self.fold_widget.layout().setContentsMargins(1,0,1,5)
        self.fold_widget.setObjectName('fold_widget')
        self.title.setObjectName('TokenLabel')
        self.setObjectName('SeeThrough')

    def connect_controls(self):
        self.layout().addWidget(self.title)
        self.layout().addWidget(self.fold_widget)
        self.title.clicked.connect(self.fold)

    def fold(self, event, fold_override=None):
        fold_override = fold_override if fold_override is not None else self.folded
        self.fold_widget.setVisible(fold_override)
        self.folded = not self.folded


class QAccordionWidget(DefaultFrame):
    fold_event = QtCore.pyqtSignal()
    itemExpanded = QtCore.pyqtSignal()
    itemCollapsed = QtCore.pyqtSignal()

    def __init__(self, parent_widget, *args, **kwargs):
        self.category_widget_lookup = {}
        super(QAccordionWidget, self).__init__(*args, **kwargs)
        self.parent_widget = parent_widget

    def create_controls(self):
        QtWidgets.QVBoxLayout(self)

    def initialize_controls(self):
        self.setObjectName('SeeThrough')
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0,0,0,0)

    def connect_controls(self):
        pass

    @property
    def category_widgets(self):
        return [widget for token, widget in iteritems(self.category_widget_lookup)]

    @property
    def categories(self):
        return list(self.category_widget_lookup)

    def is_unfolded(self):
        return all([widget.isExpanded() for token, widget in iteritems(self.category_widget_lookup)])

    def set_title(self, category, title):
        target_widget = self.category_widget_lookup.get(category.lower(), None)
        if target_widget:
            target_widget.title.setText(title)

    def fold(self, folded_objects, fold_override=None):
        for category_widget in self.category_widgets:
            category_widget.fold(None, fold_override=fold_override)

    def add_category(self, label):
        category = QAccordionCategory(label, self)
        self.layout().addWidget(category, QtCore.Qt.AlignTop)
        self.category_widget_lookup[label] = category
        self.fold_event.emit()

    def add_widget_to_category(self, category, widget):
        self.category_widget_lookup[category].fold_widget.layout().addWidget(widget)
