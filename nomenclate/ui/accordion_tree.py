import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui

from six import iteritems


class QAccordionTitle(QtWidgets.QWidget):
    clicked = QtCore.pyqtSignal()

    def __init__(self, text, tree_widget_parent, widget_item, shadow=True):
        self.widget_item = widget_item
        self.parent_tree_widget = tree_widget_parent
        super(QAccordionTitle, self).__init__(parent=tree_widget_parent)
        self.setObjectName('TokenWidgetHeader')

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.clicked.connect(self.expand)
        self.label = None
        self.set_up(text, shadow)

    def set_label(self, text):
        self.label.setText(text)

    def set_up(self, text, shadow):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignVCenter)
        label = QtWidgets.QLabel()
        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        label.setObjectName('TokenLabel')
        self.label = label
        self.layout().addWidget(label)

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()
        super(QAccordionTitle, self).mouseMoveEvent(QMouseEvent)

    def expand(self):
        self.widget_item.setExpanded(not self.widget_item.isExpanded())


class QAccordionTreeCategoryItem(QtWidgets.QTreeWidgetItem):
    def __init__(self, label, parent):
        super(QAccordionTreeCategoryItem, self).__init__()
        self.title = QtWidgets.QWidget()
        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QVBoxLayout(self.frame)

    def sizeHint(self):
        size = QtCore.QSize()
        size += self.title.sizeHint()
        size.setWidth(self.frame.sizeHint().width())
        if self.isExpanded():
            size.setHeight(self.frame.sizeHint().height() + size.height())
        return size


class QAccordionTreeWidget(QtWidgets.QTreeWidget):
    fold_event = QtCore.pyqtSignal()

    def __init__(self, parent_widget, *args, **kwargs):
        self.category_widgets = {}
        super(QAccordionTreeWidget, self).__init__(*args, **kwargs)
        self.setObjectName('AccordionTree')
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.parent_widget = parent_widget
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.header().hide()
        self.header().setSectionResizeMode(self.header().Stretch)
        self.fold_event.connect(self.sizer)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resizeColumnToContents(0)

    @property
    def categories(self):
        return list(self.category_widgets)

    def set_title(self, category, title):
        category = category.lower()
        categories = self.category_widgets
        if category in categories:
            categories.get(category).title.set_label(title)

    def fold(self, fold_state):
        for category_label in list(self.category_widgets):
            self.category_widgets[category_label].setExpanded(fold_state)
        self.fold_event.emit()

    def add_category(self, label):
        category = QAccordionTreeCategoryItem(label, self)
        category_drop_down = QtWidgets.QTreeWidgetItem()
        category.addChild(category_drop_down)

        title = QAccordionTitle(label, self, category)
        category.title = title

        self.addTopLevelItem(category)
        self.setItemWidget(category, 0, title)
        self.setItemWidget(category_drop_down, 0, category.frame)

        category_drop_down.setDisabled(True)

        self.category_widgets[label] = category
        category.setExpanded(True)

        title.clicked.connect(self.sizer)

    def add_widget_to_category(self, category, widget):
        self.category_widgets[category].layout.addWidget(widget)

    def sizeHint(self):
        size = QtCore.QSize()
        for category, item in iteritems(self.category_widgets):
            size += item.sizeHint()
        size = QtCore.QSize(size.width(), size.height())
        return size

    def resizeEvent(self, QResizeEvent):
        try:
            size = QResizeEvent.size()
        except TypeError:
            size = QResizeEvent.size
        size.setHeight(self.sizeHint().height())
        QResizeEvent.size = size
        self.parent_widget.resizeEvent(QResizeEvent)
        QtWidgets.QWidget.resizeEvent(self, QResizeEvent)

    def sizer(self):
        self.resize(self.sizeHint())
