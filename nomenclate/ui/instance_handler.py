from six import iteritems
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.accordion_tree as accordion_tree
from default import DefaultFrame

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


class TokenWidget(DefaultFrame):
    changed = QtCore.pyqtSignal(str, str, str, str, str)

    def __init__(self, token, value):
        self.token = token
        self.value = value
        super(TokenWidget, self).__init__()
        self.setMinimumWidth(50)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.add_fields()

    def resizeEvent(self, QResizeEvent):
        try:
            size = QResizeEvent.size()
        except TypeError:
            size = QResizeEvent.size
        size.setHeight(self.sizeHint().height())
        QResizeEvent.size = size

        self.setFixedHeight(self.sizeHint().height())
        QtWidgets.QWidget.resizeEvent(self, QResizeEvent)

    def sizeHint(self):
        size = QtCore.QSize()
        size.setHeight(self.value_widget.sizeHint().height() + self.accordion_tree.sizeHint().height())
        size.setWidth(super(TokenWidget, self).sizeHint().width())
        return size

    def add_fields(self):
        # if not self.token in ['var', 'version']:
        self.accordion_tree = accordion_tree.QAccordionTreeWidget(self)
        self.accordion_tree.add_category(self.token)
        self.capital = QtWidgets.QComboBox()
        self.capital.addItems(['', 'upper', 'lower'])
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.value_widget.setPlaceholderText(self.token)
        self.prefix.setValidator(utils.ALPHANUMERIC_VALIDATOR)
        self.suffix.setValidator(utils.ALPHANUMERIC_VALIDATOR)
        self.value_widget.setValidator(utils.ALPHANUMERIC_VALIDATOR)
        self.capital.currentIndexChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)

        self.accordion_tree.add_widget_to_category(self.token, self.capital)
        self.accordion_tree.add_widget_to_category(self.token, self.prefix)
        self.accordion_tree.add_widget_to_category(self.token, self.suffix)
        self.layout_main.insertWidget(0, self.accordion_tree)
        self.accordion_tree.sizer()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.value_widget = QtWidgets.QLineEdit(self.value)

    def initialize_controls(self):
        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.layout_main.setContentsMargins(1, 0, 1, 0)
        self.layout_main.setSpacing(0)

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.value_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocusProxy(self.value_widget)

    def connect_controls(self):
        self.value_widget.textChanged.connect(self.on_change)
        self.layout_main.addWidget(self.value_widget)

    def on_change(self, *args, **kwargs):
        self.value = self.value_widget.text()
        self.changed.emit(self.token,
                          self.value,
                          self.capital.currentText(),
                          self.prefix.text(),
                          self.suffix.text())

    def is_selected(self):
        return self.value_widget.hasFocus()

    def __repr__(self):
        return super(TokenWidget, self).__repr__().replace('>', ' %r>' % self.token.lower())


class InstanceHandlerWidget(DefaultFrame):
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
    def token_widgets(self):
        return [self.token_widget_lookup[token] for token in list(self.token_widget_lookup)]

    def initialize_controls(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.refresh_tokens()
        self.setObjectName('InstanceHandler')
        self.wgt_output.setObjectName('OutputWidget')
        self.wgt_output.setFixedHeight(75)
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')
        self.input_format.setPlaceholderText("Override Format String from current = %s" % self.NOM.format)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)

    def connect_controls(self):
        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)

        self.layout_main.addWidget(self.input_format)
        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)
        self.input_format.returnPressed.connect(self.set_format)

    def refresh_tokens(self):
        self.clear_tokens()
        for token, value in iteritems(self.NOM.state):
            token_widget = TokenWidget(token, value)
            self.token_widget_lookup[token] = (token_widget)

        # Add in order based on format order
        for token in self.NOM.format_order:
            token_widget = self.token_widget_lookup[token.lower()]
            token_widget.changed.connect(self.update_instance)
            self.token_layout.addWidget(token_widget)

    def clear_tokens(self):
        for i in reversed(range(self.token_layout.count())):
            self.token_layout.itemAt(i).widget().deleteLater()
        self.token_widget_lookup = {}

    def set_format(self):
        input = self.input_format.text().encode('utf-8')
        if input and len(input) > 3:
            self.NOM.format = input
            self.refresh_tokens()
            self.update_instance('', '', '', '', '')

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
