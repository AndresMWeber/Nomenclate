from default import DefaultWidget
from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
from six import iteritems

ALPHANUMERIC_VALIDATOR = QtGui.QRegExpValidator(QtCore.QRegExp('[A-Za-z0-9_]*'))


class FormatTextEdit(QtWidgets.QTextEdit):
    return_pressed = QtCore.pyqtSignal()

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_Return:
            self.return_pressed.emit()
        else:
            super(FormatTextEdit, self).keyPressEvent(QKeyEvent)


class TokenWidget(QtWidgets.QFrame):
    changed = QtCore.pyqtSignal(str, str)

    def __init__(self, token, value):
        super(TokenWidget, self).__init__()
        self.token = token

        self.setFrameShape(QtWidgets.QFrame.Box)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.layout_main = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout_main)

        self.layout_main.setContentsMargins(1, 0, 1, 0)
        self.layout_main.setSpacing(0)

        self.label = QtWidgets.QLabel(self.token.capitalize())
        self.label.setObjectName('TokenLabel')

        self.capital = QtWidgets.QCheckBox('capitalized')
        self.prefix = QtWidgets.QLineEdit(placeholderText='prefix')
        self.suffix = QtWidgets.QLineEdit(placeholderText='suffix')
        self.value = QtWidgets.QLineEdit(value)

        self.prefix.setValidator(ALPHANUMERIC_VALIDATOR)
        self.suffix.setValidator(ALPHANUMERIC_VALIDATOR)
        self.value.setValidator(ALPHANUMERIC_VALIDATOR)

        self.inner_frame = QtWidgets.QFrame()
        self.inner_frame.setFixedHeight(95)
        self.inner_frame.setFrameShape(QtWidgets.QFrame.Box)
        self.inner_frame.setFrameShadow(QtWidgets.QFrame.Sunken)

        self.inner_layout = QtWidgets.QVBoxLayout()
        self.inner_layout.addWidget(self.capital)
        self.inner_layout.addWidget(self.prefix)
        self.inner_layout.addWidget(self.suffix)
        self.inner_frame.setLayout(self.inner_layout)

        self.layout_main.addWidget(self.label)
        self.layout_main.addWidget(self.inner_frame)
        self.layout_main.addWidget(self.value)

        self.value.textChanged.connect(self.on_change)

    def on_change(self):
        value = self.value.text()
        self.changed.emit(self.token, value)


class InstanceHandlerWidget(DefaultWidget, QtWidgets.QFrame):
    TITLE = 'File List View'
    NOM = nomenclate.Nom()

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout()
        self.token_frame = QtWidgets.QFrame()
        self.wgt_output = QtWidgets.QWidget()
        self.output_layout = QtWidgets.QVBoxLayout()
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel()
        self.input_format = FormatTextEdit(placeholderText='Override Format String - Current =   %s' % self.NOM.format)
        self.token_layout = QtWidgets.QHBoxLayout()
        self.token_layout.setContentsMargins(0, 0, 0, 0)
        self.token_layout.setSpacing(0)
        self.token_widgets = []

    def initialize_controls(self):
        self.update_tokens()
        self.output_title.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')

        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.input_format.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

    def connect_controls(self):
        self.setLayout(self.layout_main)

        self.wgt_output.setLayout(self.output_layout)
        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)

        self.token_frame.setLayout(self.token_layout)
        self.layout_main.addWidget(self.input_format)
        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)
        self.input_format.return_pressed.connect(self.set_format)

    def update_tokens(self):
        self.clear_tokens()
        for token, value in iteritems(self.NOM.state):
            self.token_widgets.append(TokenWidget(token, value))

        # Add in order based on format order
        for token in self.NOM.format_order:
            for token_widget in self.token_widgets:
                if token_widget.token == token:
                    token_widget.changed.connect(self.update_instance)
                    self.token_layout.addWidget(token_widget)

    def clear_tokens(self):
        for i in reversed(range(self.token_layout.count())):
            self.token_layout.itemAt(i).widget().setParent(None)
        self.token_widgets = []

    def set_format(self):
        self.NOM.format = self.input_format.toPlainText().encode('utf-8')
        self.update_tokens()
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
