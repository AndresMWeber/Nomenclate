import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
import nomenclate.core.tools as tools
import nomenclate.ui.utils as utils
import ui.components.input_widgets as input_widgets


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidget(QtWidgets.QStackedWidget):
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
        self.format_label.setContentsMargins(0,0,50,0)
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
