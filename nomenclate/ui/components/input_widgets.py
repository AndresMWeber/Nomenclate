import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import nomenclate
import nomenclate.ui.utils as utils
from six import iteritems
from functools import partial
import nomenclate.core.tools as tools


class CustomCompleter(QtWidgets.QCompleter):
    insertText = QtCore.pyqtSignal(str, name='insertText')

    def __init__(self, options, parent=None):
        self.options = QtCore.QStringListModel(options)
        super(CustomCompleter, self).__init__(self.options, parent)
        self.popup().setStyleSheet(str('QListView{ color: rgb(200, 200, 200); '
                                       'background-color: rgba(200, 200, 200, .4);}'))
        self.setCompletionMode(self.UnfilteredPopupCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.highlighted.connect(self.setHighlighted)
        self.lastSelected = ''

    def set_items(self, items):
        self.setModel(QtCore.QStringListModel(items))

    def setHighlighted(self, text):
        self.lastSelected = text

    def getSelected(self):
        return self.lastSelected


class TokenLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args):
        super(TokenLineEdit, self).__init__(*args)
        self.completer = CustomCompleter([], parent=self)
        self.setCompleter(self.completer)
        self.set_completer_items = self.completer.set_items

    def mousePressEvent(self, QMouseClickEvent):
        self.completer.complete()
        super(TokenLineEdit, self).mousePressEvent(QMouseClickEvent)


class QLineEditContextTree(QtWidgets.QLineEdit):
    context_menu_insertion = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        self.menu = QtWidgets.QMenu()
        self.match_width = False
        super(QLineEditContextTree, self).__init__(parent)

    def resizeEvent(self, event):
        if self.match_width:
            self.menu.setMinimumWidth(self.width())
        super(QLineEditContextTree, self).resizeEvent(event)

    def contextMenuEvent(self, event):
        if self.match_width:
            self.menu.setMinimumWidth(self.width())
        self.menu.exec_(self.mapToGlobal(self.rect().bottomLeft()))

    def add_menu_item(self, menu, action_text):
        action = menu.addAction(action_text)
        action.triggered.connect(partial(self.insert_from_context_menu, action_text))
        menu.addAction(action)

    def insert_from_context_menu(self, text):
        self.context_menu_insertion.emit()
        self.setText(text)

    def build_menu_from_dict(self, menu_iterable, parent_menu=None, ignore_end_list=False):
        if parent_menu is None:
            parent_menu = QtWidgets.QMenu()
        else:
            parent_menu.clear()

        for key, value in iteritems(menu_iterable):
            sub_menu = parent_menu.addMenu(key)
            if isinstance(value, dict):
                parent_menu.addSeparator()
                self.build_menu_from_dict(value, parent_menu=sub_menu, ignore_end_list=ignore_end_list)
            elif isinstance(value, list):
                if ignore_end_list:
                    sub_menu.deleteLater()
                    self.add_menu_item(parent_menu, key)
                else:
                    for action_text in [str(_) for _ in value]:
                        self.add_menu_item(sub_menu, action_text)
            else:
                self.add_menu_item(sub_menu, str(value))

        if not isinstance(parent_menu.parent(), QtWidgets.QMenu):
            self.menu = parent_menu


class CompleterTextEntry(QLineEditContextTree):
    escapePressed = QtCore.pyqtSignal(QtCore.QEvent, name='escapePressed')
    returnPressed = QtCore.pyqtSignal(QtCore.QEvent, name='returnPressed')

    focusLost = QtCore.pyqtSignal(QtWidgets.QLineEdit)
    MODS = (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab)

    def __init__(self, parent=None):
        super(CompleterTextEntry, self).__init__(parent)
        self.completer = None
        self.complete_sub_words = False
        self.perform_validator_filter = True
        self.perform_completer_filter = True
        self.regex = None
        self.validator = None
        self._last_entry = ''
        self.set_completer_items = (lambda: None)

    def text_utf(self):
        return self.text().encode('utf-8')

    def set_mode(self, mode):
        if self.completer:
            if mode == 'unfiltered':
                self.completer.setCompletionMode(self.completer.UnfilteredPopupCompletion)
            if mode == 'filtered':
                self.completer.setCompletionMode(self.completer.PopupCompletion)

    def set_validation(self, regex):
        self.regex = QtCore.QRegExp(regex)
        self.validator = QtGui.QRegExpValidator(self.regex, self)

    def validate_input(self):
        if not self.regex:
            return True

        if self.text_input.text_utf() and not self.regex.exactMatch(self.text_input.text_utf()):
            return False
        else:
            return True

    def add_completer(self, items):
        try:
            self.completer.deleteLater()
        except AttributeError:
            pass

        self.completer = CustomCompleter(items, parent=self)
        self.completer.setWidget(self)
        self.setCompleter(self.completer)
        self.set_completer_items = self.completer.set_items
        self.set_completer_items(items)
        self.returnPressed.connect(self.completer.popup().hide)

    def mouse_completer_event(self, event):
        if self.completer:
            self.set_mode('unfiltered')
            self.completer.setCompletionPrefix("")
            self.completer.complete()

    def filter_completer(self, event):
        if self.completer and self.completer.completionModel().rowCount():
            if self.complete_sub_words:
                word = utils.find_whole_word(self.text_utf(), self.cursorPosition())
                if len(word) > 0:
                    self.completer.setCompletionPrefix(word)

    def filter_validator(self, start_text, orig_start, event):
        if self.validator:
            try:
                nomenclate.core.formatter.FormatString.get_valid_format_order(self.text_utf())
            except nomenclate.core.errors.FormatError:
                self.setText(start_text)
                self.setCursorPosition(orig_start)
            except nomenclate.core.errors.BalanceError:
                pass

    def mousePressEvent(self, QMouseClickEvent):
        if QMouseClickEvent.button() & QtCore.Qt.RightButton:
            self.completer.popup().hide()
        else:
            self.mouse_completer_event(QMouseClickEvent)
        super(CompleterTextEntry, self).mousePressEvent(QMouseClickEvent)

    def keyPressEvent(self, event):
        self.set_mode('filtered')
        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter] and self.completer.popup().isVisible():
            super(CompleterTextEntry, self).keyPressEvent(event)
            self.returnPressed.emit(event)
            return

        elif event.key() == QtCore.Qt.Key_Escape:
            self.escapePressed.emit(event)
            return

        cursor_position = self.cursorPosition()
        start_text = self.text_utf()
        super(CompleterTextEntry, self).keyPressEvent(event)

        if self.perform_validator_filter:
            self.filter_validator(start_text, cursor_position, event)
        if self.perform_completer_filter:
            self.filter_completer(event)

        self._last_entry = self.text_utf()

    def focusOutEvent(self, focus_event):
        self.focusLost.emit(self)
        super(CompleterTextEntry, self).focusOutEvent(focus_event)

    def set_options(self, options, remove_final_branch=True):
        self.build_menu_from_dict(options, ignore_end_list=remove_final_branch)
        flattened_options = list(set(tools.flattenDictToLeaves(options)))
        if self.completer:
            self.set_options(flattened_options)
        else:
            self.add_completer(flattened_options)
