from PyQt5 import QtWidgets


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

    def add_category(self, label):
        category = QtWidgets.QTreeWidgetItem()
        self.addTopLevelItem(category)
        self.setItemWidget(category, 0, QAccordionButton(label, self, category))
        frame = QtWidgets.QFrame(self)
        layout = QtWidgets.QVBoxLayout(frame)
        layout.addWidget(QtWidgets.QPushButton("Second Button"))
        layout.addWidget(QtWidgets.QPushButton("First Button"))

        container = QtWidgets.QTreeWidgetItem()
        #container.setDisabled(True)
        category.addChild(container)
        self.setItemWidget(container, 0, frame)


