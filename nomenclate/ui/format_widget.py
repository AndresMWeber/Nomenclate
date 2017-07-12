from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
import nomenclate.ui.utils as utils
import random
from six import iteritems

class FormatTextEdit(QtWidgets.QTextEdit):
    returnPressed = QtCore.pyqtSignal(QtCore.QEvent)

    def __init__(self):
        super(FormatTextEdit, self).__init__()
        self.regex = QtCore.QRegExp(utils.TOKEN_VALUE_VALIDATOR)
        self.validator = QtGui.QRegExpValidator(self.regex, self)

    @property
    def text(self):
        return self.toPlainText().encode('utf-8')

    def validate_input(self):
        if self.text_input.text and not self.regex.exactMatch(self.text_input.text):
            return False
        return True

    def keyPressEvent(self, QKeyPressEvent):
        if QKeyPressEvent.key() == QtCore.Qt.Key_Return:
            self.returnPressed.emit(QKeyPressEvent)
            return

        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        start_text = self.text

        super(FormatTextEdit, self).keyPressEvent(QKeyPressEvent)

        try:
            nomenclate.core.formatter.FormatString.get_valid_format_order(self.text)

        except nomenclate.core.errors.FormatError:
            self.setText(start_text)
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        except nomenclate.core.errors.BalanceError:
            pass


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidget(QtWidgets.QWidget):
    COLOR_LOOKUP = {}

    def __init__(self, starting_format='', *args, **kwargs):
        super(FormatWidget, self).__init__(*args, **kwargs)
        self.text_input = FormatTextEdit()
        self.format_label = FormatLabel(starting_format)

        self.returnPressed = self.text_input.returnPressed
        self.doubleClick = self.format_label.doubleClick
        self.setPlaceholderText = self.text_input.setPlaceholderText
        self.setText = self.text_input.setText

        QtWidgets.QHBoxLayout(self)
        self.layout().addWidget(self.text_input)
        self.layout().addWidget(self.format_label)

        self.returnPressed.connect(self.swap_visible_widget)
        self.format_label.doubleClick.connect(self.swap_visible_widget)
        self.text_input.setPalette(self.format_label.palette())
        self.swap_visible_widget()

    @property
    def text(self):
        return self.text_input.text

    def swap_visible_widget(self):
        text_input_hidden = self.text_input.isHidden()
        self.text_input.setVisible(text_input_hidden)
        self.format_label.setVisible(not text_input_hidden)

    def update_format(self, format_string, color_lookup):
        for format_token, color_pair in iteritems(color_lookup):
            color, rich_color = color_pair
            format_string = format_string.replace(format_token, rich_color)
        self.format_label.setText(format_string)