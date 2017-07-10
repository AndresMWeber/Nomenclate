from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.accordion_tree as accordion_tree
from default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class TokenLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args):
        super(TokenLineEdit, self).__init__(*args)
        self.completer = QtWidgets.QCompleter(parent=self)
        self.setCompleter(self.completer)
        self.completer_style_delegate = QtWidgets.QStyledItemDelegate(parent=self.completer)
        self.completer.popup().setItemDelegate(self.completer_style_delegate)
        self.completer.popup().setStyleSheet('color: rgb(200, 200, 200); background: rgba(200, 200, 200, .1);')
        self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def set_completer_items(self, items):
        self.completer.setModel(QtCore.QStringListModel(items))
        self.completer.popup().setItemDelegate(self.completer_style_delegate)
        # self.completer.popup().setStyleSheet("background-color: yellow")
        # print self.completer_style_delegate.stylesheet()
        # print self.completer_style_delegate.parent(), self.completer.parent()
        # print self.completer.popup().style(), self.completer.popup().styleSheet(), type(self.completer.popup())

    def mousePressEvent(self, QMouseClickEvent):
        self.completer.setCompletionMode(self.completer.UnfilteredPopupCompletion)
        self.completer.complete()
        self.completer.setCompletionMode(self.completer.PopupCompletion)
        super(TokenLineEdit, self).mousePressEvent(QMouseClickEvent)


class TokenWidget(DefaultFrame):
    changed = QtCore.pyqtSignal(str, str, str, str, str)

    def __init__(self, token, value):
        self.token = token.lower()
        self.value = value
        super(TokenWidget, self).__init__()
        self.add_fields()

    def create_controls(self):
        self.accordion_tree = accordion_tree.QAccordionTreeWidget(self)
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.value_widget = TokenLineEdit(self.value)

    def initialize_controls(self):
        self.setMinimumWidth(50)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)

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
        self.layout_main.insertWidget(0, self.accordion_tree)

    def add_fields(self):
        # if not self.token in ['var', 'version']:
        self.accordion_tree.add_category(self.token)
        self.capital = QtWidgets.QComboBox()
        self.capital.addItems(['caps', 'upper', 'lower'])
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.value_widget.setPlaceholderText(self.token)
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))
        self.value_widget.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.value_widget))

        self.capital.currentIndexChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)

        self.accordion_tree.add_widget_to_category(self.token, self.capital)
        self.accordion_tree.add_widget_to_category(self.token, self.prefix)
        self.accordion_tree.add_widget_to_category(self.token, self.suffix)
        self.accordion_tree.sizer()

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

    def on_change(self, *args, **kwargs):
        capital = self.capital.currentText() if self.capital.currentText != 'caps' else ''
        self.value = self.value_widget.text()
        self.changed.emit(self.token,
                          self.value,
                          capital,
                          self.prefix.text(),
                          self.suffix.text())

    def is_selected(self):
        return self.value_widget.hasFocus()

    def __repr__(self):
        return super(TokenWidget, self).__repr__().replace('>', ' %r>' % self.token.lower())
