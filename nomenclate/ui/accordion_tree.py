from PyQt5 import QtWidgets, QtCore, QtGui
from six import iteritems


class QAccordionTitle(QtWidgets.QWidget):
    GREYSCALE_COLOR = 150
    SHADOW_COLOR = 45
    COLOR_FORMAT = 'rgba({C}, {C}, {C}, 255)'
    clicked = QtCore.pyqtSignal()

    def __init__(self, text, tree_widget_parent, widget_item, shadow=True):
        self.widget_item = widget_item
        self.parent_tree_widget = tree_widget_parent
        super(QAccordionTitle, self).__init__(parent=tree_widget_parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.clicked.connect(self.expand)
        self.set_up(text, shadow)

    def set_up(self, text, shadow):
        self.setMinimumHeight(2)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.layout().setAlignment(QtCore.Qt.AlignVCenter)

        first_line = QtWidgets.QFrame()
        first_line.setFrameStyle(QtWidgets.QFrame.HLine)
        self.layout().addWidget(first_line)
        main_color = self.COLOR_FORMAT.format(C=self.GREYSCALE_COLOR)
        shadow_color = self.COLOR_FORMAT.format(C=self.SHADOW_COLOR)
        bottom_border = '' if not shadow else 'border-bottom: 1px solid %s;' % shadow_color

        style_sheet = """border: 0px solid rgba(0,0,0,0); \
                       max-height: 1px; \
                       background-color: {MAIN}; \
                       {BORDER}""".format(MAIN=main_color, BORDER=bottom_border)
        first_line.setStyleSheet(style_sheet)

        if text is None:
            return

        label = QtWidgets.QLabel()
        label.setObjectName('TokenLabel')
        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.layout().addWidget(label)

        second_line = QtWidgets.QFrame()
        second_line.setFrameStyle(QtWidgets.QFrame.HLine)
        second_line.setStyleSheet(style_sheet)
        self.layout().addWidget(second_line)

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
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.parent_widget = parent_widget
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.header().hide()
        self.fold_event.connect(self.sizer)

    @property
    def categories(self):
        return list(self.category_widgets)

    def fold(self, fold_state):
        for category_label in list(self.category_widgets):
            self.category_widgets[category_label].setExpanded(fold_state)
        self.fold_event.emit()

    def add_category(self, label):
        category = QAccordionTreeCategoryItem(label, self)
        title = QAccordionTitle(label, self, category)
        category.title = title

        self.addTopLevelItem(category)
        self.setItemWidget(category, 0, title)
        container = QtWidgets.QTreeWidgetItem()

        category.addChild(container)
        self.setItemWidget(container, 0, category.frame)

        container.setDisabled(True)

        self.category_widgets[label] = category
        category.setExpanded(True)

        title.clicked.connect(self.sizer)

    def add_widget_to_category(self, category, widget):
        self.category_widgets[category].layout.addWidget(widget)

    def sizeHint(self):
        size = QtCore.QSize()
        for category, item in iteritems(self.category_widgets):
            size += item.sizeHint()
        return size

    def resizeEvent(self, QResizeEvent):
        try:
            size = QResizeEvent.size()
        except TypeError:
            size = QResizeEvent.size
        size.setHeight(self.sizeHint().height()+50)
        QResizeEvent.size = size
        self.setColumnWidth(0, size.width())
        self.parent_widget.resizeEvent(QResizeEvent)
        QtWidgets.QWidget.resizeEvent(self, QResizeEvent)

    def sizer(self):
        self.resize(self.sizeHint())
