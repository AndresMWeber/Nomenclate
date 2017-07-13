import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import nomenclate


class CustomCompleter(QtWidgets.QCompleter):
    insertText = QtCore.pyqtSignal(str)

    def __init__(self, options, parent=None):
        self.options = QtCore.QStringListModel(options)
        super(CustomCompleter, self).__init__(self.options, parent)
        self.popup().setStyleSheet(str('QListView{ color: rgb(200, 200, 200); '
                                       'background-color: rgba(200, 200, 200, .4);}'))
        self.setCompletionMode(self.UnfilteredPopupCompletion)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def set_items(self, items):
        self.setModel(QtCore.QStringListModel(items))


class TokenLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args):
        super(TokenLineEdit, self).__init__(*args)
        self.completer = CustomCompleter([], parent=self)
        self.set_completer_items = self.completer.set_items

    def mousePressEvent(self, QMouseClickEvent):
        self.completer.complete()
        super(TokenLineEdit, self).mousePressEvent(QMouseClickEvent)


class CompleterTextEntry(QtWidgets.QLineEdit):
    returnPressed = QtCore.pyqtSignal(QtCore.QEvent, name='returnPressed')
    MODS = (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return, QtCore.Qt.Key_Escape, QtCore.Qt.Key_Tab, QtCore.Qt.Key_Backtab)

    def __init__(self, parent=None):
        super(CompleterTextEntry, self).__init__(parent)
        self.completer = None
        self.regex = None
        self.validator = None
        self.set_completer_items = (lambda: None)

    @property
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

        if self.text_input.text_utf and not self.regex.exactMatch(self.text_input.text_utf):
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
        self.completer.insertText.connect(self.insertCompletion)
        self.set_completer_items = self.completer.set_items
        self.set_completer_items(items)

    def insertCompletion(self, completion):
        if self.completer:
            tc = self.cursor()
            extra = (len(completion) - len(self.completer.completionPrefix()))
            tc.movePosition(QtGui.QTextCursor.Left)
            tc.movePosition(QtGui.QTextCursor.EndOfWord)
            tc.insert(completion[-extra:])
            self.setCursorPosition(tc.start)
            self.completer.popup().hide()

    def mouse_completer_event(self, event):
        if self.completer:
            self.set_mode('unfiltered')
            self.completer.setCompletionPrefix("")
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            self.completer.complete()

    def filter_completer(self, event):
        if self.completer:
            self.set_mode('filtered')
            word = self.find_whole_word(self.cursorPosition())
            cr = self.cursorRect()

            if len(word) > 0:
                self.completer.setCompletionPrefix(word)
                popup = self.completer.popup()
                popup.setCurrentIndex(self.completer.completionModel().index(0, 0))

                cr.setWidth(self.completer.popup().sizeHintForColumn(0)
                            + self.completer.popup().verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
            else:
                self.completer.popup().hide()

    def find_whole_word(self, cursor_position):
        start_position = cursor_position
        text = self.text_utf
        end, start = start_position, start_position
        
        for index, char in enumerate(text[start_position:]):
            abs_index = start_position + index
            if char in nomenclate.settings.SEPARATORS or abs_index == len(text) - 1:
                index = index + 1 if abs_index == len(text) - 1 else index
                end = start_position + index
                break

        for index, char in enumerate(reversed(text[0:start_position])):
            index+=1
            abs_index = start_position - index
            if char in nomenclate.settings.SEPARATORS or abs_index == 0:
                index = index if abs_index == 0 else index - 1
                start = start_position - index
                break
        return text[start:end]


    def filter_validator(self, start_text, orig_start, event):
        if self.validator:
            try:
                nomenclate.core.formatter.FormatString.get_valid_format_order(self.text_utf)
            except nomenclate.core.errors.FormatError:
                self.setText(start_text)
                self.setCursorPosition(orig_start)
            except nomenclate.core.errors.BalanceError:
                pass

    def mousePressEvent(self, QMouseClickEvent):
        self.mouse_completer_event(QMouseClickEvent)
        super(CompleterTextEntry, self).mousePressEvent(QMouseClickEvent)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Tab and self.completer.popup().isVisible():
            self.completer.insertText.emit(self.completer.getSelected())
            self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
            return

        if event.key() == QtCore.Qt.Key_Return:
            self.returnPressed.emit(event)
            return

        cursor_position = self.cursorPosition()
        start_text = self.text_utf
        super(CompleterTextEntry, self).keyPressEvent(event)
        self.filter_validator(start_text, cursor_position, event)
        self.filter_completer(event)
