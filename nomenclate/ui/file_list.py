import os
from default import DefaultWidget
from PyQt5 import QtWidgets, QtGui, QtCore


class QFileItem(QtGui.QStandardItem):
    def __init__(self, path):
        if os.path.exists(path):
            self.long_path = os.path.normpath(path)
            self.short_path = os.path.basename(self.long_path)
            super(QFileItem, self).__init__(self.short_path)
        else:
            raise IOError('Input %s is not a valid file path' % path)


class QFileItemModel(QtGui.QStandardItemModel):
    FULL = True

    @property
    def items(self):
        return [self.itemFromIndex(self.index(row_index, 0)) for row_index in range(self.rowCount())]

    def appendRow(self, q_file_item):
        if any([q_file_item.long_path == row_item.long_path for row_item in self.items]):
            return
        super(QFileItemModel, self).appendRow(self.set_item_path(q_file_item))

    def display_full(self):
        self.FULL = not self.FULL
        for item in self.items:
            self.set_item_path(item)

    def set_item_path(self, item):
        if self.FULL:
            item.setText(item.long_path)
        else:
            item.setText(item.short_path)
        return item


class FileListWidget(DefaultWidget):
    TITLE = 'File List View'

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()
        self.wgt_list_view = QtWidgets.QListView()
        self.list = QFileItemModel()
        self.proxy_list = QtCore.QSortFilterProxyModel()
        self.btn_widget = QtWidgets.QWidget()
        self.btn_layout = QtWidgets.QHBoxLayout()
        self.wgt_filter_list = QtWidgets.QLineEdit(placeholderText='filter...')
        self.btn_clear = QtWidgets.QPushButton('Clear')
        self.btn_remove = QtWidgets.QPushButton('Remove')
        self.btn_full = QtWidgets.QPushButton('Full Path')

    def initialize_controls(self):
        self.setAcceptDrops(True)
        self.wgt_list_view.setAlternatingRowColors(True)
        self.wgt_list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def connect_controls(self):
        self.setLayout(self.layout_main)

        self.proxy_list.setSourceModel(self.list)
        self.wgt_list_view.setModel(self.proxy_list)

        self.layout_main.addWidget(self.wgt_filter_list)
        self.layout_main.addWidget(self.wgt_list_view)
        self.layout_main.addWidget(self.btn_widget)

        self.btn_widget.setLayout(self.btn_layout)
        self.btn_layout.addWidget(self.btn_clear)
        self.btn_layout.addWidget(self.btn_full)
        self.btn_layout.addWidget(self.btn_remove)

        self.btn_remove.clicked.connect(self.remove_selected_items)
        self.btn_clear.clicked.connect(self.clear_model)
        self.btn_full.clicked.connect(self.list.display_full)
        self.wgt_filter_list.textChanged.connect(self.update_regexp)
        self.list.itemChanged.connect(self.sort_model)

    def update_regexp(self):
        self.proxy_list.setFilterRegExp(QtCore.QRegExp(str(self.wgt_filter_list.text()),
                                                       QtCore.Qt.CaseInsensitive,
                                                       QtCore.QRegExp.FixedString))

    def sort_model(self):
        self.list.sort(QtCore.Qt.AscendingOrder)

    def remove_selected_items(self):
        remove_rows = []
        for model_index in self.wgt_list_view.selectedIndexes():
            for row_index in range(self.list.rowCount()):
                list_model_index = self.list.index(row_index, 0)
                item = self.list.itemFromIndex(list_model_index)
                if item.short_path == model_index.data() or item.long_path == model_index.data():
                    remove_rows.append(QtCore.QPersistentModelIndex(list_model_index))

        for persistent_row_index in remove_rows:
            self.list.removeRow(persistent_row_index.row())

    def clear_model(self):
        self.list.clear()

    def update_file_paths(self, links):
        for link in links:
            item = QFileItem(link)
            self.list.appendRow(item)
