import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import nomenclate.core.tools as tools
import nomenclate.ui.utils as utils
import ui.components.input_widgets as input_widgets


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidgetOld(QtWidgets.QStackedWidget):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)
    format_updated = QtCore.pyqtSignal()
    COLOR_LOOKUP = {}

    def __init__(self, starting_format='', *args, **kwargs):
        super(FormatWidget, self).__init__(*args, **kwargs)
        self.text_input = input_widgets.CompleterTextEntry()
        self.text_input.set_validation(utils.TOKEN_VALUE_VALIDATOR)
        self.format_label = FormatLabel(starting_format)

        self.escapePressed = self.text_input.escapePressed
        self.returnPressed = self.text_input.returnPressed
        self.doubleClick = self.format_label.doubleClick
        self.setPlaceholderText = self.text_input.setPlaceholderText
        self.setText = self.text_input.setText

        self.addWidget(self.text_input)
        self.addWidget(self.format_label)

        self.setContentsMargins(0, 0, 0, 0)
        self.format_label.setContentsMargins(0, 0, 50, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.returnPressed.connect(self.swap_visible_widget)
        self.text_input.focusLost.connect(self.swap_visible_widget)
        self.format_label.doubleClick.connect(self.swap_visible_widget)
        self.text_input.setPalette(self.format_label.palette())
        self.swap_visible_widget()

        self.text_input.setObjectName('FormatWidgetInput')
        self.format_label.setObjectName('FormatWidgetOutput')
        self.setObjectName('FormatWidgetStack')

    @property
    def text(self):
        return self.text_input.text_utf

    def swap_visible_widget(self):
        self.setCurrentIndex(not self.layout().currentIndex())

    def update_format(self, format_string, color_lookup, format_order):
        last_position = 0
        for format_token in format_order:
            color, rich_color = color_lookup[format_token]
            pre_slice = format_string[:last_position]
            work_slice = format_string[last_position:]
            old_length = len(format_string)

            last_position = len(pre_slice) + work_slice.index(format_token) + len(format_token)
            format_string = pre_slice + work_slice.replace(format_token, rich_color, 1)
            last_position += len(format_string) - old_length
        self.format_label.setText(format_string)

    def set_options(self, options):
        self.text_input.add_completer(list(tools.flattenDictToLeaves(options)))

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidget(input_widgets.CompleterTextEntry):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)
    format_updated = QtCore.pyqtSignal()
    COLOR_LOOKUP = {}

    def __init__(self, starting_format='', *args, **kwargs):
        super(FormatWidget, self).__init__(*args, **kwargs)
        self.perform_completer_filter = False
        self.perform_validator_filter = True

        self.format_colored = False
        self.set_validation(utils.TOKEN_VALUE_VALIDATOR)
        self.setContentsMargins(0, 0, 50, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.setObjectName('FormatWidgetInput')

        self.returnPressed.connect(self.swap_mode)
        self.focusLost.connect(self.swap_mode)
        self.doubleClick.connect(self.swap_mode)
        self.textChanged.connect(self.on_paste)

        self.format = ''
        self._last_text = ''
        self.setText(str(starting_format))
        self.format_updated.emit()

    def on_paste(self):
        self.detect_paste_event(self._last_text, self.text_utf())

    def setText(self, new_text):
        super(FormatWidget, self).setText(new_text)

    def detect_paste_event(self, old_text, new_text):
        print 'detect paste event'
        self.format = self.text_utf()
        if len(new_text.replace(old_text, '')) > 1:
            self.format_colored = False
            self.swap_mode()
        self._last_text = new_text

    def keyPressEvent(self, event):
        super(FormatWidget, self).keyPressEvent(event)
        self._last_text = self.text_utf()

    def swap_mode(self):
        if self.format_colored:
            self.setText(self.format)
        else:
            print 'emitting format'
            self.format_updated.emit()
        self.format_colored = not self.format_colored

    def update_format_colors(self, format_string, rich_text_format_string, color_lookup, format_order):
        # self.setReadOnly(False)
        print 'updating format colors'
        self.format = str(format_string)
        last_position = 0
        """
        for format_token in format_order:
            color, rich_color = color_lookup[format_token]
            pre_slice = format_string[:last_position]
            work_slice = format_string[last_position:]
            old_length = len(format_string)

            last_position = len(pre_slice) + work_slice.index(format_token) + len(format_token)
            format_string = pre_slice + work_slice.replace(format_token, rich_color, 1)
            last_position += len(format_string) - old_length
        """
        formats = []

        f = QtGui.QTextCharFormat()
        f.setFontWeight(QtGui.QFont.Bold)
        fr_task = QtGui.QTextLayout.FormatRange()
        fr_task.start = 0
        fr_task.length = 4
        fr_task.format = f

        f.setFontItalic(True)
        f.setBackground(QtCore.Qt.darkYellow)
        f.setForeground(QtCore.Qt.white)

        fr_tracker = QtGui.QTextLayout.FormatRange()
        fr_tracker.start = 5
        fr_tracker.length = 7
        fr_tracker.format = f

        formats.append(fr_task)
        formats.append(fr_tracker)

        self.setLineEditTextFormat(formats)
        # self.setText(format_string)
        # self.setReadOnly(True)

    def set_options(self, options):
        self.add_completer(list(tools.flattenDictToLeaves(options)))

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatWidget, self).mousePressEvent(QMousePressEvent)

    def setLineEditTextFormat(self, formats):
        attributes = []
        for format_range in formats:
            type = QtGui.QInputMethodEvent.TextFormat
            start = format_range.start
            length = format_range.length
            value = format_range.format
            print start, length, value, type
            attributes.append(QtGui.QInputMethodEvent.Attribute(type, start, length, value))

        event = QtGui.QInputMethodEvent("", attributes)
        QtCore.QCoreApplication.sendEvent(self, event)
        QtWidgets.QApplication.sendEvent(self, event)

    def inputMethodEvent(self, event):
        print 'READ HERE READ HERE'
        print event.attributes(), event.replacementStart()
        return super(FormatWidget, self).inputMethodEvent(event)