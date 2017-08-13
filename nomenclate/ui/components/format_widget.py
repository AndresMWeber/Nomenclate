import Qt.QtCore as QtCore
import Qt.QtWidgets as QtWidgets
import nomenclate.core.tools as tools
import nomenclate.ui.utils as utils
import nomenclate.ui.components.input_widgets as input_widgets


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.Signal(QtCore.QEvent)
    rightClick = QtCore.Signal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)

    def mousePressEvent(self, QMouseClickEvent):
        if QMouseClickEvent.button() & QtCore.Qt.RightButton:
            self.rightClick.emit(QMouseClickEvent)
        super(FormatLabel, self).mousePressEvent(QMouseClickEvent)


class FormatWidget(QtWidgets.QStackedWidget):
    COLOR_LOOKUP = {}
    format_updated = QtCore.Signal()

    def __init__(self, starting_format='', parent=None, *args, **kwargs):
        super(FormatWidget, self).__init__(parent=parent, *args, **kwargs)
        self.text_input = input_widgets.CompleterTextEntry()
        self.text_input.set_validation(utils.TOKEN_VALUE_VALIDATOR)
        self.format_label = FormatLabel(starting_format)
        self.format_label.rightClick.connect(self.text_input.mousePressEvent)

        self._last_text = ''
        self.text_input.setText(starting_format)

        self.escapePressed = self.text_input.escapePressed
        self.returnPressed = self.text_input.returnPressed
        self.doubleClick = self.format_label.doubleClick
        self.setPlaceholderText = self.text_input.setPlaceholderText

        self.addWidget(self.text_input)
        self.addWidget(self.format_label)

        self.setToolTip('Double-Click to edit Token Format String')
        self.setContentsMargins(0, 0, 0, 0)
        self.format_label.setContentsMargins(0, 0, 50, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.text_input.setPalette(self.format_label.palette())

        self.format_label.rightClick.connect(self.swap_visible_widget)
        self.text_input.context_menu_insertion.connect(self.swap_visible_widget)
        self.text_input.textChanged.connect(self.text_changed)
        self.escapePressed.connect(self.swap_visible_widget)
        self.returnPressed.connect(self.swap_visible_widget)
        self.format_label.doubleClick.connect(self.swap_visible_widget)
        self.swap_visible_widget()

        self.text_input.setObjectName('FormatWidgetInput')
        self.format_label.setObjectName('FormatWidgetOutput')
        self.setObjectName('FormatWidgetStack')

    @property
    def text_utf(self):
        return self.text_input.text_utf()

    def text_changed(self, text):
        matches = tools.get_string_difference(self._last_text, text)
        if len(max(text, self._last_text)) - len(matches) > 1 and not self.text_input.completer.popup().isVisible():
            self.format_updated.emit()
        self._last_text = text

    def setText(self, text):
        self.text_input.setText(text)
        self.format_updated.emit()

    def swap_visible_widget(self):
        self.format_updated.emit()
        self.setCurrentIndex(not self.layout().currentIndex())

    def update_format_colors(self, format_string, rich_text_format_string, color_lookup, format_order):
        last_position = 0
        for format_token in format_order:
            _, rich_color = color_lookup[format_token]
            pre_slice = format_string[:last_position]
            work_slice = format_string[last_position:]
            old_length = len(format_string)

            last_position = len(pre_slice) + work_slice.index(format_token) + len(format_token)
            format_string = pre_slice + work_slice.replace(format_token, rich_color, 1)
            last_position += len(format_string) - old_length

        self.format_label.setText(format_string)
