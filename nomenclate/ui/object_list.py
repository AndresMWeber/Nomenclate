from functools import partial
import Qt.QtCore as QtCore
import Qt.QtGui as QtGui
import Qt.QtWidgets as QtWidgets
import nomenclate.ui.platforms as platforms
import nomenclate.settings as settings
from nomenclate.ui.components.object_model import QFileItemModel
from nomenclate.ui.utils import REGISTERED_INCREMENTER_TOKENS
from nomenclate.ui.components.default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.DEBUG

LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)


class QFileRenameTreeView(QtWidgets.QTreeView):
    sorting_stale = QtCore.Signal()
    request_state = QtCore.Signal(QtCore.QPoint, QtGui.QStandardItem)
    proxy_filter_modified = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(QFileRenameTreeView, self).__init__(*args, **kwargs)
        self.proxy_row_count = self.last_proxy_row_count = 0
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
        self.sorting_stale.connect(self.base_model.order_changed)

    def onCustomContextMenu(self, qpoint):
        index = self.indexAt(qpoint)
        if index.isValid():
            object_path_index = self.base_model.index(index.row(), 0)
            item = self.base_model.itemFromIndex(object_path_index)
            self.request_state.emit(qpoint, item)

    def context_menu_for_item(self, qpoint, item, nomenclate_instance):
        context_menu = QtWidgets.QMenu()
        context_menu.clear()
        all_actions = []
        for token in nomenclate_instance.format_order:
            lower_token = token.lower()
            for token in REGISTERED_INCREMENTER_TOKENS:
                if token in lower_token:
                    LOG.debug('Context Menu: token %s detected as incrementer' % lower_token)
                    action = context_menu.addAction('increment with %s' % lower_token)
                    action.triggered.connect(partial(self.set_items_incrementer, lower_token, True))
                    all_actions.append(lower_token)

        if all_actions:
            context_menu.addSeparator()
            for lower_token in all_actions:
                LOG.debug('Context Menu: adding all action for token %s' % lower_token)
                all_action = context_menu.addAction(u'increment ALL with %s' % lower_token)
                all_action.triggered.connect(partial(self.set_items_incrementer, lower_token, False))

        context_menu.exec_(self.mapToGlobal(qpoint))

    def reset_incrementer(self):
        for row in self.base_model.data_table:
            row[0].increment_token = ""

    def set_items_incrementer(self, token, selected=True):
        row_range = [index.row() for index in self.selectedIndexes()] if selected else range(
            self.proxy_model.rowCount())
        for row in row_range:
            selected_index = self.base_model.index(row, 0)
            self.base_model.itemFromIndex(selected_index).increment_token = token
        self.proxy_filter_modified.emit()

    def update_regexp(self, regex):
        self.filter_regex.setPattern(regex)
        self.proxy_model.setFilterRegExp(self.filter_regex)
        self.proxy_filter_modified.emit()

    def check_rows(self):
        self.proxy_row_count = self.proxy_model.rowCount()
        if self.proxy_row_count != self.last_proxy_row_count:
            self.proxy_filter_modified.emit()
        self.last_proxy_row_count = self.proxy_row_count

    @property
    def object_paths(self):
        object_paths = []
        for row in range(self.base_model.rowCount()):
            object_paths.append(QtCore.QPersistentModelIndex(self.base_model.index(row, 0)).data())
        return object_paths

    def get_item(self, row, column):
        persistent_index = QtCore.QPersistentModelIndex(self.base_model.index(row, column))
        return self.base_model.item(persistent_index.row(), persistent_index.column())

    def add_paths(self, object_paths):
        for object_path in object_paths:
            self.base_model.appendRow(object_path)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
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
        row_data = item.takeRow(row)
        item.insertRow(newRow, row_data)


class FileListWidget(DefaultFrame):
    update_object_paths = QtCore.Signal(list)
    request_name = QtCore.Signal(QtGui.QStandardItem, int, dict)
    request_state = QtCore.Signal(QtCore.QPoint, QtCore.QModelIndex)
    renamed = QtCore.Signal()
    TITLE = 'File List View'

    def get_selected_rows(self):
        return [QtCore.QPersistentModelIndex(index).row() for index in self.wgt_list_view.selectedIndexes() if
                index.column() == 0]

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_list_view = QFileRenameTreeView(parent=self)
        self.btn_widget = QtWidgets.QFrame(parent=self)
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
        self.reset_incrementer = self.wgt_list_view.reset_incrementer

        self.btn_remove.clicked.connect(self.wgt_list_view.remove_selected_items)
        self.btn_rename.clicked.connect(self.action_rename_items)

        self.btn_clear.clicked.connect(self.wgt_list_view.base_model.clear)
        self.btn_full.clicked.connect(self.wgt_list_view.base_model.display_full)
        self.wgt_filter_list.textChanged.connect(self.wgt_list_view.update_regexp)
        self.update_object_paths.connect(self.wgt_list_view.add_paths)

        self.wgt_list_view.proxy_filter_modified.connect(self.get_object_names)

        self.context_menu_for_item = self.wgt_list_view.context_menu_for_item

    def action_rename_items(self, btn_event=None, auto_confirm=True):
        selected_rows = self.get_selected_rows()
        if selected_rows:
            if not auto_confirm:
                message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                                    "Rename Items",
                                                    "Do you want to rename %d items" % len(selected_rows),
                                                    parent=self)

                message_box.addButton(QtWidgets.QMessageBox.Yes)
                message_box.addButton(QtWidgets.QMessageBox.No)
                auto_confirm = message_box.exec_()

            if auto_confirm:
                for row in selected_rows:
                    name_item, new_name_item = self.wgt_list_view.get_item(row, 0), self.wgt_list_view.get_item(row, 1)
                    name, new_name = name_item.text(), new_name_item.text()

                    try:
                        if not new_name:
                            raise NameError('No new object name specified for %d:%s' % (row, name))
                        new_name = platforms.current.rename(name, new_name)
                        name_item.setText(new_name)
                        LOG.info('Success renaming object: %d:%s->%s' % (row, name, new_name))

                    except (OSError, NameError) as e:
                        LOG.warning('Failed renaming object %d:%s error: %s' % (row, name, e))
                self.renamed.emit()

    def populate_objects(self, object_paths):
        self.update_object_paths.emit(object_paths)

    def get_object_names(self):
        token_counter = {}
        for row, items in enumerate(self.wgt_list_view.filtered_data_table()):
            object_item, _ = items
            override_dict = {}
            token = getattr(object_item, 'increment_token', None)

            if token is not None:
                token_counter[token] = token_counter.get(token, 0) + 1
                override_dict[token] = token_counter[token]

            self.request_name.emit(object_item, row, override_dict)

    @staticmethod
    def set_item_name(object_item, object_name):
        object_item.update_target_name(object_name)
