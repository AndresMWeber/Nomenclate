from ui.default import DefaultWidget
from PyQt5 import QtWidgets, QtGui, QtCore


class FileSystemWidget(DefaultWidget):
    TITLE = 'Filesystem View'
    send_files = QtCore.pyqtSignal(list)

    def create_controls(self):
        self.model = QtWidgets.QFileSystemModel()
        self.tree = QtWidgets.QTreeView()
        self.window_layout = QtWidgets.QVBoxLayout()
        self.btn_add = QtWidgets.QPushButton('Add Files')
        self.filter = QtCore.QSortFilterProxyModel()

    def initialize_controls(self):
        self.tree.setWindowTitle("Dir")
        self.setWindowTitle(self.category_label)

        self.model.setRootPath('')

        self.tree.setAnimated(False)
        self.tree.setIndentation(20)
        self.tree.setSortingEnabled(True)

    def connect_controls(self):
        self.filter.setSourceModel(self.model)
        self.tree.setModel(self.filter)
        self.window_layout.addWidget(self.tree)
        self.setLayout(self.window_layout)
        self.btn_add.clicked.connect(self.push_files)

    def push_files(self):
        self.send_files.emit([item.text() for item in self.tree.selectedItems()])
