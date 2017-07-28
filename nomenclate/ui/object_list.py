import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
from nomenclate.ui.components.object_model import QFileItemModel
from nomenclate.ui.default import DefaultFrame


class QFileRenameTreeView(QtWidgets.QTreeView):
    sorting_stale = QtCore.pyqtSignal()
    request_state = QtCore.pyqtSignal(QtCore.QPoint, QtGui.QStandardItem)

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

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomContextMenu)

        # Connections
        self.sorting_stale.connect(self.base_model.sorting_stale)

    def onCustomContextMenu(self, qpoint):
        index = self.indexAt(qpoint)
        if index.isValid():
            object_path_index = self.base_model.index(index.row(), 0)
            item = self.base_model.itemFromIndex(object_path_index)
            self.request_state.emit(qpoint, item)

    def context_menu_for_item(self, qpoint, item, nomenclate_instance):
        context_menu = QtWidgets.QMenu()
        for token in nomenclate_instance.format_order:
            lower_token = token.lower()
            if 'var' in lower_token or 'version' in lower_token:
                context_menu.addAction(lower_token)
                # TODO: add action here to increment only based on specific vars.
                print(getattr(nomenclate_instance, lower_token))

        context_menu.exec_(self.mapToGlobal(qpoint))

    def update_regexp(self, regex):
        self.filter_regex.setPattern(regex)
        self.proxy_model.setFilterRegExp(self.filter_regex)

    @property
    def object_paths(self):
        object_paths = []
        for row in range(self.base_model.rowCount()):
            object_paths.append(QtCore.QPersistentModelIndex(self.base_model.index(row, 0)).data())
        return object_paths

    def add_paths(self, object_paths):
        for object_path in object_paths:
            self.base_model.appendRow(object_path)
        self.sorting_stale.emit()

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
        self.sorting_stale.emit()

    def filtered_data_table(self):
        index_table = []
        for row in range(self.proxy_model.rowCount()):
            index_table.append([])
            for column in range(self.proxy_model.columnCount()):
                proxy_index = self.proxy_model.index(row, column)
                base_model_item = self.base_model.itemFromIndex(self.proxy_model.mapToSource(proxy_index))
                index_table[row].append(base_model_item)
        return index_table

    def moveRow(self, moveUp):
        item = self.base_model
        row = self.currentIndex().row()
        if (moveUp and row == 0):
            return

        newRow = row - 1
        list = item.takeRow(row)
        item.insertRow(newRow, list)


class FileListWidget(DefaultFrame):
    update_object_paths = QtCore.pyqtSignal(list)
    request_name = QtCore.pyqtSignal(QtGui.QStandardItem, int, dict)
    request_state = QtCore.pyqtSignal(QtCore.QPoint, QtCore.QModelIndex)
    TITLE = 'File List View'

    @property
    def selected_items(self):
        return [QtCore.QPersistentModelIndex(index).data() for index in self.wgt_list_view.selectedIndexes()]

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_list_view = QFileRenameTreeView()
        self.btn_widget = QtWidgets.QFrame()
        self.btn_layout = QtWidgets.QHBoxLayout(self.btn_widget)
        self.btn_layout.setContentsMargins(0, 0, 0, 0)
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
        self.request_state = self.wgt_list_view.request_state
        self.btn_remove.clicked.connect(self.wgt_list_view.remove_selected_items)
        self.btn_rename.clicked.connect(self.action_rename_items)

        self.btn_clear.clicked.connect(self.wgt_list_view.base_model.clear)
        self.btn_full.clicked.connect(self.wgt_list_view.base_model.display_full)
        self.wgt_filter_list.textChanged.connect(self.wgt_list_view.update_regexp)
        self.update_object_paths.connect(self.wgt_list_view.add_paths)
        self.context_menu_for_item = self.wgt_list_view.context_menu_for_item

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

    def populate_objects(self, object_paths):
        self.update_object_paths.emit(object_paths)

    def get_object_names(self):
        row_index = 0
        for object_item, rename_item in self.wgt_list_view.filtered_data_table():
            print(object_item.text(), row_index)
            self.request_name.emit(object_item, row_index, {})
            row_index += 1

    def set_item_name(self, object_item, object_name):
        object_item.update_target_name(object_name)
