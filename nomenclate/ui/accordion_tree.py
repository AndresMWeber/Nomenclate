from PyQt5 import QtWidgets, QtCore, QtGui


class QAccordionTitle(QtWidgets.QWidget):
    GREYSCALE_COLOR = 150
    SHADOW_COLOR = 45
    COLOR_FORMAT = 'rgba({C}, {C}, {C}, 255)'
    clicked = QtCore.pyqtSignal()

    def __init__(self, text, tree_widget_parent, widget_item, shadow=True):
        self.widget_item = widget_item
        super(QAccordionTitle, self).__init__(parent=tree_widget_parent)
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
        text_width = label.fontMetrics()
        width = text_width.width(text) + 6

        label.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.layout().addWidget(label)

        second_line = QtWidgets.QFrame()
        second_line.setFrameStyle(QtWidgets.QFrame.HLine)
        second_line.setStyleSheet(style_sheet)
        self.layout().addWidget(second_line)

    def mousePressEvent(self, QMouseEvent):
        self.clicked.emit()

    def expand(self):
        self.widget_item.setExpanded(not self.widget_item.isExpanded())


class QAccordionButton(QtWidgets.QPushButton):
    def __init__(self, text, tree_widget_parent, widget_item):
        self.widget_item = widget_item
        super(QAccordionButton, self).__init__(text, tree_widget_parent)
        self.clicked.connect(self.expand)

    def expand(self):
        self.widget_item.setExpanded(not self.widget_item.isExpanded())


class QAccordionTreeWidget(QtWidgets.QTreeWidget):
    def __init__(self, *args, **kwargs):
        super(QAccordionTreeWidget, self).__init__(*args, **kwargs)
        self.setRootIsDecorated(False)
        self.setIndentation(0)
        self.header().close()
        self.category_layouts = {}

    def add_category(self, label):
        category = QtWidgets.QTreeWidgetItem()
        self.addTopLevelItem(category)
        self.setItemWidget(category, 0, QAccordionTitle(label, self, category))
        frame = QtWidgets.QFrame(self)
        layout = QtWidgets.QVBoxLayout(frame)
        container = QtWidgets.QTreeWidgetItem()
        container.setDisabled(True)
        category.addChild(container)
        self.setItemWidget(container, 0, frame)

        self.category_layouts[label] = layout

    def add_widget_to_category(self, category, widget):
        self.category_layouts[category].addWidget(widget)
