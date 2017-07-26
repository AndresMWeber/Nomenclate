import os
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from nomenclate.ui.default import DefaultFrame



class QFileItem(QtGui.QStandardItem):
    def __init__(self, path):
        self.path = path
        super(QFileItem, self).__init__(self.path)
        self.setEditable(False)

    def split_non_alpha(split_string, reverse=False):
        end_pos = 0 if not reverse else len(split_string)
        char_index = len(split_string) - 1 if not reverse else 1
        while char_index >= end_pos and split_string[char_index].isalpha():
            char_index -= 1
        return (split_string[:char_index], split_string[char_index:])

    @property
    def long_path(self):
        if self.os_mode:
            return os.path.normpath(self.path)
        else:
            return self.path

    @property
    def short_path(self):
        if self.os_mode:
            return os.path.basename(self.path)
        else:
            return self.split_non_alpha(self.path)

    @property
    def os_mode(self):
        return self.is_valid and (self.is_file or self.is_dir)

    @property
    def is_valid(self):
        return os.path.exists(self.path)

    @property
    def is_file(self):
        return os.path.isfile(self.path)

    @property
    def is_dir(self):
        return os.path.isdir(self.path)


class QFileItemModel(QtGui.QStandardItemModel):
    FULL_PATH = True

    def __init__(self):
        super(QFileItemModel, self).__init__()
        self.setColumnCount(2)

    @property
    def object_paths(self):
        return [self.itemFromIndex(self.index(row_index, 0)) for row_index in range(self.rowCount())]

    @property
    def data_table(self):
        index_table = []
        for row in range(self.rowCount()):
            index_table.append([])
            for column in range(self.columnCount()):
                index_table[row].append(self.itemFromIndex(self.index(row, column)))
        return index_table

    def appendRow(self, row_entry):
        entry_object_path, entry_label = row_entry
        entry_object_path = QFileItem(entry_object_path)

        for row_item in self.data_table:
            object_path, label = row_item
            if entry_object_path.long_path == object_path.long_path:
                label.setText(entry_label)
                return

        self.set_item_path(entry_object_path)
        super(QFileItemModel, self).appendRow([entry_object_path, QtGui.QStandardItem(entry_label)])

    def display_full(self):
        self.FULL_PATH = not self.FULL_PATH
        for item in self.object_paths:
            self.set_item_path(item)

    def set_item_path(self, item):
        if self.FULL_PATH:
            item.setText(item.long_path)
        else:
            item.setText(item.short_path)
        return item


class QFileRenameTreeView(QtWidgets.QTreeView):
    def __init__(self, *args, **kwargs):
        super(QFileRenameTreeView, self).__init__(*args, **kwargs)

        # Creating
        self.proxy_model = QtCore.QSortFilterProxyModel()
        self.base_model = QFileItemModel()
        self.filter_regex = QtCore.QRegExp("", QtCore.Qt.CaseInsensitive, QtCore.QRegExp.FixedString)

        # Settings
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.proxy_model.setSourceModel(self.base_model)
        self.setModel(self.proxy_model)
        self.proxy_model.setFilterRegExp(self.filter_regex)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

        # Connections
        self.base_model.itemChanged.connect(self.sort_model)

    def update_regexp(self, regex):
        self.filter_regex.setPattern(regex)
        self.proxy_model.setFilterRegExp(self.filter_regex)

    @property
    def object_paths(self):
        object_paths = []
        for row in range(self.base_model.rowCount()):
            object_paths.append(QtCore.QPersistentModelIndex(self.base_model.index(row, 0)).data())
        return object_paths

    def remove_selected_items(self):
        remove_rows = []
        for selected_index in self.selectedIndexes():
            for row_index in range(self.base_model.rowCount()):
                model_index = self.base_model.index(row_index, 0)
                item = self.base_model.itemFromIndex(model_index)
                if selected_index.data() in [item.short_path, item.long_path]:
                    remove_rows.append(QtCore.QPersistentModelIndex(model_index))

        for persistent_row_index in remove_rows:
            self.model().removeRow(persistent_row_index.row())

    def sort_model(self):
        self.model().sort(QtCore.Qt.AscendingOrder)


class FileListWidget(DefaultFrame):
    TITLE = 'File List View'

    @property
    def selected_items(self):
        return [QtCore.QPersistentModelIndex(index).data() for index in self.wgt_list_view.selectedIndexes()]

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_list_view = QFileRenameTreeView()
        self.btn_widget = QtWidgets.QFrame()
        self.btn_layout = QtWidgets.QHBoxLayout(self.btn_widget)
        self.btn_layout.setContentsMargins(0,0,0,0)
        self.wgt_filter_list = QtWidgets.QLineEdit(placeholderText='filter...')
        self.btn_clear = QtWidgets.QPushButton('Clear')
        self.btn_remove = QtWidgets.QPushButton('Remove')
        self.btn_full = QtWidgets.QPushButton('Full Path')
        self.btn_rename = QtWidgets.QPushButton('Rename Selected Items')

    def initialize_controls(self):
        self.setAcceptDrops(True)
        self.layout_main.addWidget(self.wgt_filter_list)
        self.layout_main.addWidget(self.wgt_list_view)
        self.layout_main.addWidget(self.btn_widget)
        self.layout_main.addWidget(self.btn_rename)

        self.setObjectName('ObjectListFrame')
        self.setContentsMargins(0, 0, 0, 0)
        self.btn_layout.addWidget(self.btn_clear)
        self.btn_layout.addWidget(self.btn_full)
        self.btn_layout.addWidget(self.btn_remove)

    def connect_controls(self):
        self.btn_remove.clicked.connect(self.wgt_list_view.remove_selected_items)
        self.btn_rename.clicked.connect(self.action_rename_items)

        self.btn_clear.clicked.connect(self.wgt_list_view.base_model.clear)
        self.btn_full.clicked.connect(self.wgt_list_view.base_model.display_full)
        self.wgt_filter_list.textChanged.connect(self.wgt_list_view.update_regexp)

    def action_rename_items(self):
        selected_items = self.selected_items
        if selected_items:
            message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                                "Rename Items",
                                                "Do you want to rename %d items" % len(selected_items),
                                                parent=self)

            message_box.addButton(QtWidgets.QMessageBox.Yes)
            message_box.addButton(QtWidgets.QMessageBox.No)
            # message_box.setInformativeText("Do you really want to disable safety enforcement?")
            ret = message_box.exec_()
            if ret:
                print('If this were active we would rename these items: %s' % selected_items)

    def update_object_paths(self, link_label_pair):
        for pair in link_label_pair:
            self.wgt_list_view.base_model.appendRow(pair)
