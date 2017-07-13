import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import nomenclate.ui.input_widgets as input_widgets
import nomenclate.ui.utils as utils
import nomenclate.core.tools as tools
from six import iteritems


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatLabel, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidget(QtWidgets.QWidget):
    COLOR_LOOKUP = {}

    def __init__(self, starting_format='', *args, **kwargs):
        super(FormatWidget, self).__init__(*args, **kwargs)
        self.text_input = input_widgets.CompleterTextEntry()
        self.text_input.set_validation(utils.TOKEN_VALUE_VALIDATOR)
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
        return self.text_input.text_utf

    def swap_visible_widget(self):
        text_input_hidden = self.text_input.isHidden()
        self.text_input.setVisible(text_input_hidden)
        self.format_label.setVisible(not text_input_hidden)

    def update_format(self, format_string, color_lookup):
        for format_token, color_pair in iteritems(color_lookup):
            color, rich_color = color_pair
            format_string = format_string.replace(format_token, rich_color)
        self.format_label.setText(format_string)

    def set_options(self, options):
        self.text_input.add_completer(list(tools.flattenDictToLeaves(options)))
