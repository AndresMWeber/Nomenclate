from six import add_metaclass, iteritems
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import nomenclate.ui.components.input_widgets as input_widgets
import nomenclate.settings as settings
import nomenclate.ui.utils as utils
import ui.components.accordion_widget as accordion_tree
from nomenclate.ui.default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class TokenWidgetFactory(QtCore.pyqtWrapperType):
    TOKEN_WIDGETS = {}

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)
        token = dct.get('HANDLES_TOKEN', 'default')
        if token:
            mcs.TOKEN_WIDGETS[token] = cls
        return cls

    @classmethod
    def get_token_widget(cls, token, value):
        WidgetToken = cls.TOKEN_WIDGETS.get('default')
        for handles_token in list(cls.TOKEN_WIDGETS):
            query_token = token
            if handles_token in query_token.lower() or ('(' in token and ')' in token and handles_token == 'static'):
                WidgetToken = cls.TOKEN_WIDGETS[handles_token]
                break
        return WidgetToken(token, value)


@add_metaclass(TokenWidgetFactory)
class TokenWidget(DefaultFrame):
    CAPITAL_OPTIONS = ['case', 'upper', 'lower']
    changed = QtCore.pyqtSignal(dict)

    def __init__(self, token, value):
        self.SETTINGS = {}
        self.token = token.lower()
        self.value = value
        self.value_widget = None
        super(TokenWidget, self).__init__()
        self.value_widget.setObjectName(self.token + 'ValueInput')

    def create_controls(self):
        self.accordion_tree = accordion_tree.QAccordionWidget(self)
        QtWidgets.QVBoxLayout(self)

    def set_category_title(self, category, title):
        self.accordion_tree.set_title(category, title)

    def initialize_controls(self):
        self.setObjectName('TokenWidget')
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self.accordion_tree.add_category(self.token)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.SETTINGS['token'] = lambda: self.token

    def connect_controls(self):
        self.layout().addWidget(self.accordion_tree, 0, QtCore.Qt.AlignTop)
        self.layout().addWidget(self.value_widget)

    def add_fields(self):
        raise NotImplementedError

    def on_change(self, *args, **kwargs):
        serialized = self.serialize()
        self.value = serialized.get('value', None)
        self.changed.emit(serialized)

    def serialize(self):
        settings = {}
        for setting, value in iteritems(self.SETTINGS):
            if isinstance(value, dict):
                value = value.get(utils.GETTER)
            value = value() if callable(value) else value
            settings[setting] = value.encode('utf-8') if hasattr(value, 'encode') else value

        return settings

    def is_selected(self):
        return self.value_widget.hasFocus()

    def add_default_values_from_config(self, default_values_dict):
        for default_key, default_value in iteritems(default_values_dict):
            setter = self.SETTINGS.get(default_key, {}).get(utils.SETTER, None)
            if callable(setter):
                setter(default_value)

    def set_options(self, options):
        if isinstance(options, list):
            options = {'options': options}
        if getattr(self.value_widget, 'set_options', None):
            self.value_widget.set_options(options, for_token=True)

    def __repr__(self):
        return super(TokenWidget, self).__repr__().replace('>', ' %r>' % self.token.lower())


class DefaultTokenWidget(TokenWidget):
    def create_controls(self):
        super(DefaultTokenWidget, self).create_controls()
        self.capital = QtWidgets.QComboBox()
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()
        self.length = QtWidgets.QSpinBox()
        self.value_widget = input_widgets.CompleterTextEntry(self.value)

    def initialize_controls(self):
        super(DefaultTokenWidget, self).initialize_controls()
        self.value_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.value_widget.setPlaceholderText(self.token)
        self.value_widget.add_completer([])
        self.value_widget.set_validation(utils.TOKEN_VALUE_VALIDATOR)
        self.setFocusProxy(self.value_widget)

        self.length.setMinimum(1)
        self.length.setPrefix('length ')
        self.length.setSpecialValueText('short')
        self.length.hide()

        self.capital.addItems(self.CAPITAL_OPTIONS)
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))

        self.accordion_tree.add_widgets_to_category(self.token, [self.capital, self.prefix, self.suffix, self.length])

        # Register with internal token settings dictionary to allow auto-serialization
        self.SETTINGS['value'] = {utils.GETTER: self.value_widget.text, utils.SETTER: self.value_widget.setText}
        self.SETTINGS['%s_len' % self.token] = {utils.GETTER: self.length.value, utils.SETTER: self.length.setValue}

        self.SETTINGS['prefix_setting'] = {utils.GETTER: self.prefix.text, utils.SETTER: self.prefix.setText}
        self.SETTINGS['suffix_setting'] = {utils.GETTER: self.suffix.text, utils.SETTER: self.suffix.setText}
        self.SETTINGS['case_setting'] = {
            utils.GETTER: lambda: self.capital.currentText() if self.capital.currentIndex() != 0 else "",
            utils.SETTER: self.capital.setCurrentIndex}

    def connect_controls(self):
        super(DefaultTokenWidget, self).connect_controls()
        self.value_widget.textChanged.connect(self.on_change)
        self.length.valueChanged.connect(self.on_change)
        self.value_widget.options_added.connect(self.length.show)
        self.capital.currentIndexChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)


class VarTokenWidget(TokenWidget):
    HANDLES_TOKEN = 'var'

    def create_controls(self):
        super(VarTokenWidget, self).create_controls()
        self.capital = QtWidgets.QComboBox()
        self.value_widget = QtWidgets.QSpinBox()
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()

    def initialize_controls(self):
        super(VarTokenWidget, self).initialize_controls()
        self.capital.addItems(self.CAPITAL_OPTIONS)
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))

        self.accordion_tree.add_widgets_to_category(self.token,
                                                    [self.capital, self.prefix, self.suffix, self.value_widget])
        # Register with internal token settings dictionary to allow auto-serialization
        self.SETTINGS['case_setting'] = {
            utils.GETTER: lambda: self.capital.currentText() if self.capital.currentIndex() != 0 else "",
            utils.SETTER: self.capital.setCurrentText}
        self.SETTINGS['prefix_setting'] = {utils.GETTER: self.prefix.text, utils.SETTER: self.prefix.setText}
        self.SETTINGS['suffix_setting'] = {utils.GETTER: self.suffix.text, utils.SETTER: self.suffix.setText}
        self.SETTINGS['value'] = {utils.GETTER: self.value_widget.value, utils.SETTER: self.value_widget.setValue}

    def connect_controls(self):
        super(VarTokenWidget, self).connect_controls()
        self.capital.currentIndexChanged.connect(self.on_change)
        self.value_widget.setValue(0)
        self.value_widget.valueChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)


class VersionTokenWidget(TokenWidget):
    HANDLES_TOKEN = 'version'

    def create_controls(self):
        super(VersionTokenWidget, self).create_controls()
        self.identifier = QtWidgets.QComboBox()
        self.padding = QtWidgets.QSpinBox()
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()
        self.value_widget = QtWidgets.QSpinBox()

    def initialize_controls(self):
        super(VersionTokenWidget, self).initialize_controls()
        self.identifier.addItems(['0-9', 'A-Z', 'a-z'])
        list_view = QtWidgets.QListView(self.identifier)
        list_view.setObjectName('drop_down_list_view')
        self.identifier.setView(list_view)

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))

        self.accordion_tree.add_widgets_to_category(self.token,
                                                    [self.identifier,
                                                     self.padding,
                                                     self.prefix,
                                                     self.suffix])
        self.padding.setMinimum(1)
        # Register with internal token settings dictionary to allow auto-serialization
        self.SETTINGS['prefix_setting'] = {utils.GETTER: self.prefix.text, utils.SETTER: self.prefix.setText}
        self.SETTINGS['suffix_setting'] = {utils.GETTER: self.suffix.text, utils.SETTER: self.suffix.setText}
        self.SETTINGS['value'] = {utils.GETTER: self.value_widget.value, utils.SETTER: self.value_widget.setValue}
        self.SETTINGS['identifier_setting'] = {utils.GETTER: self.identifier.currentText,
                                               utils.SETTER: self.capital.setCurrentText}
        self.SETTINGS['%s_padding' % self.token] = {utils.GETTER: self.padding.value,
                                                    utils.SETTER: self.padding.setValue}
        self.SETTINGS['%s_format' % self.token] = {utils.GETTER: lambda: '#', utils.SETTER: lambda x: None}

    def connect_controls(self):
        super(VersionTokenWidget, self).connect_controls()
        self.value_widget.valueChanged.connect(self.on_change)
        self.identifier.currentIndexChanged.connect(self.on_change)
        self.padding.valueChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)


class DateTokenWidget(TokenWidget):
    HANDLES_TOKEN = 'date'

    def create_controls(self):
        super(DateTokenWidget, self).create_controls()
        self.capital = QtWidgets.QComboBox()
        self.prefix = QtWidgets.QLineEdit()
        self.suffix = QtWidgets.QLineEdit()
        self.length = QtWidgets.QSpinBox()
        self.value_widget = input_widgets.CompleterTextEntry(self.value)

    def initialize_controls(self):
        super(DateTokenWidget, self).initialize_controls()
        self.value_widget.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.value_widget.setPlaceholderText(self.token)
        self.value_widget.add_completer([])
        self.value_widget.set_validation(utils.TOKEN_VALUE_VALIDATOR)
        self.setFocusProxy(self.value_widget)

        self.length.setMinimum(1)
        self.capital.addItems(self.CAPITAL_OPTIONS)
        list_view = QtWidgets.QListView(self.capital)
        list_view.setObjectName('drop_down_list_view')
        self.capital.setView(list_view)

        self.prefix.setPlaceholderText('prefix')
        self.suffix.setPlaceholderText('suffix')
        self.prefix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.prefix))
        self.suffix.setValidator(QtGui.QRegExpValidator(utils.TOKEN_VALUE_VALIDATOR, self.suffix))

        self.accordion_tree.add_widgets_to_category(self.token, [self.capital, self.prefix, self.suffix, self.length])

        # Register with internal token settings dictionary to allow auto-serialization
        self.SETTINGS['value'] = self.value_widget.text
        self.SETTINGS['%s_len' % self.token] = self.length.value
        self.SETTINGS['prefix_setting'] = self.prefix.text
        self.SETTINGS['suffix_setting'] = self.suffix.text
        self.SETTINGS['case_setting'] = lambda: self.capital.currentText() if self.capital.currentIndex() != 0 else ""

    def connect_controls(self):
        super(DateTokenWidget, self).connect_controls()
        self.value_widget.textChanged.connect(self.on_change)
        self.value_widget.setReadOnly(True)
        self.length.valueChanged.connect(self.on_change)
        self.capital.currentIndexChanged.connect(self.on_change)
        self.prefix.textChanged.connect(self.on_change)
        self.suffix.textChanged.connect(self.on_change)


class StaticTokenWidget(TokenWidget):
    HANDLES_TOKEN = 'static'

    def create_controls(self):
        super(StaticTokenWidget, self).create_controls()
        self.value_widget = QtWidgets.QLineEdit()
        self.disabled_label = QtWidgets.QLabel('Cannot change')

    def initialize_controls(self):
        super(StaticTokenWidget, self).initialize_controls()
        self.accordion_tree.add_widgets_to_category(self.token, [self.disabled_label])

    def connect_controls(self):
        super(StaticTokenWidget, self).connect_controls()
        self.value_widget.selectionChanged.connect(lambda: self.value_widget.deselect())
        self.value_widget.setText(self.token)
        self.value_widget.setReadOnly(True)
