import os
import Qt.QtGui as QtGui
import Qt.QtCore as QtCore
import nomenclate.ui.utils as utils
import nomenclate.ui.platforms as platforms
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.INFO

LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)


class QObjectItem(QtGui.QStandardItem):
    def __init__(self, path):
        self.path = path
        super(QObjectItem, self).__init__(self.path)
        self.rename_item = QtGui.QStandardItem('')
        self.setDragEnabled(False)
        self.setEditable(False)
        self.rename_item.setEditable(False)
        self.set_icon()

    def split_non_alpha(split_string, reverse=False):
        """ Searches backward or forward for a non alpha character and returns the string based on that position
            to the front or back depending on direction.
        """
        end_pos = 0 if not reverse else len(split_string)
        char_index = len(split_string) - 1 if not reverse else 1
        while char_index >= end_pos and split_string[char_index].isalpha():
            char_index -= 1
        return (split_string[:char_index], split_string[char_index:])

    def set_icon(self):
        if self.is_dir:
            icon = utils.ICON_FOLDER
        elif self.is_file:
            icon = utils.ICON_FILE
        else:
            icon = utils.ICON_OBJECT

        if icon:
            self.setIcon(utils.get_icon(icon))

    def update_target_name(self, name):
        self.rename_item.setText(name)

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
        return platforms.current.exists(self.path)

    @property
    def is_file(self):
        return os.path.isfile(self.path)

    @property
    def is_dir(self):
        return os.path.isdir(self.path)


class QFileItemModel(QtGui.QStandardItemModel):
    FULL_PATH = True
    order_changed = QtCore.Signal()

    def __init__(self):
        super(QFileItemModel, self).__init__()
        self.setColumnCount(2)
        self.order_changed.connect(self.refresh)

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

    def refresh(self):
        self.remove_stale_references()
        self.default_sort()

    def entry_exists(self, object_path):
        for row_item in self.data_table:
            row_object_path, _ = row_item
            if os.path.normpath(object_path) == row_object_path.text():
                return True
        return False

    def removeRow(self, index):
        super(QFileItemModel, self).removeRow(index)
        self.order_changed.emit()

    def appendRow(self, object_path):
        if self.entry_exists(object_path):
            return
        entry_object_path = QObjectItem(object_path)
        self.set_item_path(entry_object_path)
        super(QFileItemModel, self).appendRow([entry_object_path, entry_object_path.rename_item])
        self.order_changed.emit()

    def default_sort(self):
        self.sort(0, QtCore.Qt.AscendingOrder)

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

    def remove_stale_references(self):
        for row_item in self.data_table:
            row_object_path, _ = row_item
            if not platforms.current.exists(row_object_path.text()):
                self.removeRow(row_object_path.index().row())
