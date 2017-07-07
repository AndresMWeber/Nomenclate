from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
import nomenclate.ui.utils as utils
import nomenclate.ui.token_widget as token_wgt
import nomenclate.settings as settings
from default import DefaultWidget

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class FormatTextEdit(QtWidgets.QLineEdit):
    return_pressed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(FormatTextEdit, self).__init__(*args, **kwargs)
        self.setValidator(utils.ALPHANUMERIC_VALIDATOR)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Return:
            self.return_pressed.emit()
        else:
            super(FormatTextEdit, self).keyPressEvent(QKeyEvent)



class InstanceHandlerWidget(DefaultWidget):
    TITLE = 'File List View'
    NOM = nomenclate.Nom()
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_output = QtWidgets.QWidget()
        self.output_layout = QtWidgets.QVBoxLayout(self.wgt_output)
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel()
        self.input_format = QtWidgets.QLineEdit()
        self.token_frame = QtWidgets.QFrame()
        self.token_layout = QtWidgets.QHBoxLayout(self.token_frame)
        self.token_layout.setContentsMargins(0, 0, 0, 0)
        self.token_layout.setSpacing(0)
        self.token_widget_lookup = {}

    @property
    def user_format_override(self):
        return self.input_format.text().encode('utf-8')

    @property
    def active_token_widgets(self):
        return [self.token_widget_lookup[token] for token in list(self.token_widget_lookup)
                if self.token_widget_lookup[token].parent()]

    @property
    def token_widgets(self):
        return [self.token_widget_lookup[token] for token in list(self.token_widget_lookup)]

    def initialize_controls(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.refresh_active_token_widgets()

        self.setObjectName('InstanceHandler')
        self.wgt_output.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')

        self.input_format.setPlaceholderText("Override Format String from current = %s" % self.NOM.format)

    def connect_controls(self):
        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)

        self.layout_main.addWidget(self.input_format)
        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)
        self.input_format.returnPressed.connect(self.set_format)

    def refresh_active_token_widgets(self):

        for token, value in [(token, self.NOM.state[token.lower()]) for token in self.NOM.format_order]:
            self.LOG.info('Running through token value pair %s:%s' % (token, value))
            token_widget = self.token_widget_lookup.get(token, None)
            if token_widget is None:
                self.LOG.debug('No preexisting token widget...creating and adding to %s.token_widget_lookup.' % self)
                token_widget = token_wgt.TokenWidget(token, value)
                self.token_widget_lookup[token] = token_widget
            else:
                self.token_layout.addWidget(token_widget)

            receiversCount = token_widget.receivers(token_widget.changed)
            if receiversCount == 0:
                self.LOG.info('Connecting %s.changed -> %s.update_instance and adding to layout' % (token_widget, self))
                token_widget.changed.connect(self.update_instance)
                self.token_layout.addWidget(token_widget)

    def clear_stale_token_widgets(self):
        self.LOG.debug('Comparing current token widgets %s against format order %s' % (self.token_widgets,
                                                                                       self.NOM.format_order))
        for token_widget in self.active_token_widgets:
            if token_widget.token not in self.NOM.format_order:
                self.LOG.debug('widget %s.deleteLater as it is stale.' % token_widget)
                token_widget.deleteLater()
                self.token_widget_lookup.pop(token_widget.token)
            else:
                self.LOG.debug('Recycle widget %s as it is still relevant and should not be deleted.' % token_widget)
                self.token_layout.removeWidget(token_widget)

    def set_format(self):
        input_format = self.user_format_override
        if input_format and len(input_format) > 3:
            self.NOM.format = input_format
        self.refresh()

    def refresh(self):
        self.clear_stale_token_widgets()
        self.refresh_active_token_widgets()
        self.update_instance("", "", "", "", "")

    def update_instance(self, token, value, capitalized='', prefix='', suffix=''):
        if any([token, capitalized, prefix, suffix]):
            self.NOM.merge_dict({token.encode('utf-8'): value.encode('utf-8')})
            token_attr = getattr(self.NOM, token)
            token_attr.case_setting = capitalized
            token_attr.prefix_setting = prefix
            token_attr.suffix_setting = suffix

        formatted = str("<html><head><meta name=\"qrichtext\" content=\"1\" /></head>"
                        "<body style=\" white-space: pre-wrap; font-family:Sans Serif; "
                        "font-size:9pt; font-weight:400; font-style:normal; text-decoration:none;\">"
                        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; "
                        "margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:20pt;\">{NAME}</p>"
                        "</body></html>")
        self.output_name.setText(formatted.format(NAME=self.NOM.get()))

    def select_next_token_line_edit(self, direction):
        order = self.NOM.format_order
        direction_shifted_tokens = order[-1:] + order[:-1] if direction else order[1:] + order[:1]
        restart = order[-1] if direction else order[0]
        for token, next_token in zip(order, direction_shifted_tokens):
            token_widget = self.token_widget_lookup[token.lower()]
            if token_widget.is_selected() and restart != next_token:
                next_widget = self.token_widget_lookup[next_token.lower()]
                self.LOG.debug(
                    'Selecting from widget %r to next token widget (%s): %r' % (token_widget, next_token, next_widget))
                next_widget.value_widget.setFocus()
                return True
        return False
