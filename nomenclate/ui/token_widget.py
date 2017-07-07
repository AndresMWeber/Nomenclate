from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate.ui.utils as utils
import nomenclate.settings as settings
import nomenclate.ui.accordion_tree as accordion_tree
from default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class OptionsCompleter(QtWidgets.QCompleter):
    def __init__(self, parent, all_tags):
        super(OptionsCompleter, self).__init__(self, all_tags, parent)
        self.all_tags = set(all_tags)
        self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)

    def update(self, options, completion_prefix):
        options = list(self.all_tags.difference(options))
        model = QtWidgets.QStringListModel(options, self)
        self.setModel(model)

        self.setCompletionPrefix(completion_prefix)
        if completion_prefix.strip() != '':
            self.complete()


class TokenLineEdit(QtWidgets.QLineEdit):
    text_modified = QtCore.pyqtSignal(QtCore.QObject, QtCore.QObject)

    def __init__(self, *args):
        super(TokenLineEdit, self).__init__(self, *args)
        self.textChanged.connect(self, self.text_changed)

        options_completer = OptionsCompleter(self, ['test', 'mest', 'fest'])
        options_completer.activated.connect(self.complete_text)
        self.text_changed.connect(options_completer.update)
    def text_changed(self, text):
        all_text = text
        text = all_text[:self.cursorPosition()]
        prefix = text.split(',')[-1].strip()

        text_tags = []
        for t in all_text.split(','):
            t1 = t.strip()
            if t1 != '':
                text_tags.append(t)
        text_tags = list(set(text_tags))
        self.text_modified.emit(text_tags, prefix)

    def complete_text(self, text):
        cursor_pos = self.cursorPosition()
        before_text = self.text()[:cursor_pos]
        after_text = self.text()[cursor_pos:]
        prefix_len = len(before_text.split(',')[-1].strip())
        self.setText('%s%s, %s' % (before_text[:cursor_pos - prefix_len], text, after_text))
        self.setCursorPosition(cursor_pos - prefix_len + len(text) + 2)


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
        self.value_widget = QtWidgets.QLineEdit(self.value)

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