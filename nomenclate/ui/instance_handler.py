from default import DefaultFrame
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
from six import iteritems

ALPHANUMERIC_VALIDATOR = QtGui.QRegExpValidator(QtCore.QRegExp('[A-Za-z0-9_]*'))


class FormatTextEdit(QtWidgets.QLineEdit):
    return_pressed = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(FormatTextEdit, self).__init__(*args, **kwargs)
        self.setValidator(ALPHANUMERIC_VALIDATOR)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Return:
            self.return_pressed.emit()
        else:
            super(FormatTextEdit, self).keyPressEvent(QKeyEvent)


class TokenWidget(DefaultFrame):
    changed = QtCore.pyqtSignal(str, str)

    def __init__(self, token, value):
        self.token = token
        self.value = value
        super(TokenWidget, self).__init__()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel(self.token.capitalize())
        self.inner_frame = QtWidgets.QFrame()
        self.inner_layout = QtWidgets.QVBoxLayout(self.inner_frame)

        self.capital = QtWidgets.QCheckBox('capitalized')
        self.prefix = QtWidgets.QLineEdit(placeholderText='prefix')
        self.suffix = QtWidgets.QLineEdit(placeholderText='suffix')
        self.value_widget = QtWidgets.QLineEdit(self.value)

        self.options = QtWidgets.QToolBox()
        self.options_widget = QtWidgets.QWidget()
        self.options_layout = QtWidgets.QVBoxLayout(self.options_widget)

    def initialize_controls(self):
        self.label.setObjectName('TokenLabel')

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.layout_main.setContentsMargins(1, 0, 1, 0)
        self.layout_main.setSpacing(0)

        self.inner_frame.setFixedHeight(95)
        self.inner_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.inner_frame.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.prefix.setValidator(ALPHANUMERIC_VALIDATOR)
        self.suffix.setValidator(ALPHANUMERIC_VALIDATOR)
        self.value_widget.setValidator(ALPHANUMERIC_VALIDATOR)

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.inner_frame.setFocusPolicy(QtCore.Qt.NoFocus)
        self.options_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.options.setFocusPolicy(QtCore.Qt.NoFocus)
        self.capital.setFocusPolicy(QtCore.Qt.NoFocus)
        self.prefix.setFocusPolicy(QtCore.Qt.NoFocus)
        self.suffix.setFocusPolicy(QtCore.Qt.NoFocus)

        self.value_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocusProxy(self.value_widget)

    def connect_controls(self):
        self.value_widget.textChanged.connect(self.on_change)

        self.layout_main.addWidget(self.label)
        self.layout_main.addWidget(self.inner_frame)
        self.layout_main.addWidget(self.value_widget)

        self.options.addItem(self.options_widget, 'Token Options')
        self.options_layout.addWidget(self.capital)
        self.options_layout.addWidget(self.prefix)
        self.options_layout.addWidget(self.suffix)

        self.inner_layout.addWidget(self.options)
        print(self.children())

    def on_change(self):
        self.value = self.value_widget.text()
        self.changed.emit(self.token, self.value)

    def is_selected(self):
        return self.value_widget.hasFocus()

    def __repr__(self):
        return super(TokenWidget, self).__repr__().replace('>', ' %r>' % self.token.lower())


class InstanceHandlerWidget(DefaultFrame):
    TITLE = 'File List View'
    NOM = nomenclate.Nom()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_output = QtWidgets.QWidget()
        self.output_layout = QtWidgets.QVBoxLayout(self.wgt_output)
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel()
        self.input_format = QtWidgets.QLineEdit(placeholderText='Override Format String - Current =   %s' %
                                                                self.NOM.format)
        self.token_frame = QtWidgets.QFrame()
        self.token_layout = QtWidgets.QHBoxLayout(self.token_frame)
        self.token_layout.setContentsMargins(0, 0, 0, 0)
        self.token_layout.setSpacing(0)
        self.token_widgets = {}

    def initialize_controls(self):
        self.refresh_tokens()
        self.setObjectName('InstanceHandler')
        self.wgt_output.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')

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
            self.token_widgets[token] = (token_widget)

        # Add in order based on format order
        for token in self.NOM.format_order:
            token_widget = self.token_widgets[token.lower()]
            token_widget.changed.connect(self.update_instance)
            self.token_layout.addWidget(token_widget)

    def clear_tokens(self):
        for i in reversed(range(self.token_layout.count())):
            self.token_layout.itemAt(i).widget().deleteLater()
        self.token_widgets = {}

    def set_format(self):
        self.NOM.format = self.input_format.toPlainText().encode('utf-8')
        self.refresh_tokens()
        self.update_instance('', '')

    def update_instance(self, token, value):
        self.NOM.merge_dict({token.encode('utf-8'): value.encode('utf-8')})
        formatted = str("<html><head><meta name=\"qrichtext\" content=\"1\" /></head>"
                        "<body style=\" white-space: pre-wrap; font-family:Sans Serif; "
                        "font-size:9pt; font-weight:400; font-style:normal; text-decoration:none;\">"
                        "<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; "
                        "margin-right:0px; -qt-block-indent:0; text-indent:0px; font-size:20pt;\">{NAME}</p>"
                        "</body></html>")
        self.output_name.setText(formatted.format(NAME=self.NOM.get()))

    def select_next_token_line_edit(self):
        for token, next_token in zip(self.NOM.format_order, self.NOM.format_order[1:] + [self.NOM.format_order[0]]):
            token_widget = self.token_widgets[token.lower()]
            if token_widget.is_selected():
                next_widget = self.token_widgets[next_token.lower()]
                print('selecting from widget %r to next widget %r %s' % (token_widget, next_widget, next_token))
                next_widget.value_widget.setFocus()
                return
