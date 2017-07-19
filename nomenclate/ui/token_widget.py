import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.input_widgets as input_widgets
import nomenclate.ui.accordion_widget as accordion_tree
from default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class TokenWidget(DefaultFrame):
    changed = QtCore.pyqtSignal(str, str, str, str, str)

    def __init__(self, token, value):
        self.token = token.lower()
        self.value = value
        super(TokenWidget, self).__init__()
        self.add_fields()

    def create_controls(self):
        self.accordion_tree = accordion_tree.QAccordionWidget(self)
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.value_widget = input_widgets.CompleterTextEntry(self.value)

    def set_category_title(self, category, title):
        self.accordion_tree.set_title(category, title)

    def initialize_controls(self):
        self.setObjectName('TokenWidget')
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.value_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocusProxy(self.value_widget)

    def connect_controls(self):
        self.value_widget.textChanged.connect(self.on_change)
        self.layout_main.addWidget(self.accordion_tree, 0, QtCore.Qt.AlignTop)
        self.layout_main.addWidget(self.value_widget)

    def add_fields(self):
        # TODO: modify version/var specific rollouts here.
        # if not self.token in ['var', 'version']:
        self.accordion_tree.add_category(self.token)
        self.capital = QtWidgets.QComboBox()
        self.capital.addItems(['case', 'upper', 'lower'])
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))
        self.value_widget.setPlaceholderText(self.token)
        self.value_widget.add_completer([])
        self.value_widget.set_validation(utils.TOKEN_VALUE_VALIDATOR)

        self.capital.currentIndexChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)

        self.accordion_tree.add_widget_to_category(self.token, self.capital)
        self.accordion_tree.add_widget_to_category(self.token, self.prefix)
        self.accordion_tree.add_widget_to_category(self.token, self.suffix)

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
