from PyQt5 import QtWidgets, QtCore, QtGui
import nomenclate
import nomenclate.ui.utils as utils
import nomenclate.ui.token_widget as token_wgt
import nomenclate.settings as settings
from default import DefaultWidget

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class FormatTextEdit(QtWidgets.QTextEdit):
    returnPressed = QtCore.pyqtSignal(QtCore.QEvent)

    def __init__(self):
        super(FormatTextEdit, self).__init__()
        self.regex = QtCore.QRegExp(utils.TOKEN_VALUE_VALIDATOR)
        self.validator = QtGui.QRegExpValidator(self.regex, self)

    @property
    def text(self):
        return self.toPlainText()

    def validate_input(self):
        if self.text_input.text and not self.regex.exactMatch(self.text_input.text):
            return False
        return True

    def keyPressEvent(self, QKeyPressEvent):
        if QKeyPressEvent.key() == QtCore.Qt.Key_Return:
            self.returnPressed.emit(QKeyPressEvent)
            return

        cursor = self.textCursor()
        start, end = cursor.selectionStart(), cursor.selectionEnd()
        start_text = self.text

        super(FormatTextEdit, self).keyPressEvent(QKeyPressEvent)

        try:
            nomenclate.core.formatter.FormatString.get_valid_format_order(self.text)

        except nomenclate.core.errors.FormatError:
            self.setText(start_text)
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        except nomenclate.core.errors.BalanceError:
            pass


class FormatLabel(QtWidgets.QLabel):
    doubleClick = QtCore.pyqtSignal(QtCore.QEvent)

    def mouseDoubleClickEvent(self, QMousePressEvent):
        self.doubleClick.emit(QMousePressEvent)
        super(FormatTextEdit, self).mouseDoubleClickEvent(QMousePressEvent)


class FormatWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(FormatTextEdit, self).__init__(*args, **kwargs)
        self.text_input = FormatWidget()
        self.format_label = FormatLabel()

        self.returnPressed = self.text_input.returnPressed
        self.doubleClick = self.format_label.doubleClick
        self.setPlaceholderText = self.text_input.setPlaceholderText
        self.setText = self.text_input.setText

        QtWidgets.QHBoxLayout(self)
        self.layout().addWidget(self.text_input)
        self.layout().addWidget(self.format_label)

        self.returnPressed.connect(self.swap_visible_widget)
        self.format_label.doubleClick.connect(self.swap_visible_widget)

        self.setText('test<span style="color:#ff0000;">test</span>')
        self.swap_visible_widget()

    def swap_visible_widget(self):
        print 'either click or return was pressed'
        text_input_hidden = self.text_input.isHidden()
        self.text_input.setVisible(text_input_hidden)
        self.format_label.setVisible(not text_input_hidden)


class InstanceHandlerWidget(DefaultWidget):
    TITLE = 'File List View'
    NOM = nomenclate.Nom()
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    nomenclate_output = QtCore.pyqtSignal(str)

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_output = QtWidgets.QWidget()
        self.output_layout = QtWidgets.QVBoxLayout(self.wgt_output)
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel()
        self.input_format = FormatTextEdit()
        self.token_frame = QtWidgets.QFrame()
        self.token_layout = QtWidgets.QHBoxLayout(self.token_frame)
        self.token_layout.setContentsMargins(0, 0, 0, 0)
        self.token_layout.setSpacing(0)
        self.token_widget_lookup = {}
        self.fold_state = True

    @property
    def user_format_override(self):
        return self.input_format.toPlainText().encode('utf-8')

    @property
    def active_token_widgets(self):
        return [self.token_widget_lookup[token] for token in list(self.token_widget_lookup)
                if self.token_widget_lookup[token].parent()]

    @property
    def token_widgets(self):
        return [self.token_widget_lookup[token] for token in list(self.token_widget_lookup)]

    def get_index(self, index):
        return self.NOM.get() + str(index)

    def fold(self):
        self.fold_state = not self.fold_state
        for token_widget in self.active_token_widgets:
            token_widget.accordion_tree.fold(self.fold_state)

    def initialize_controls(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.refresh_active_token_widgets()

        self.setObjectName('InstanceHandler')
        self.wgt_output.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')
        self.nomenclate_output.connect(self.set_output)
        msg = "DOUBLE CLICK TO MODIFY CURRENT FORMAT: %s" % self.NOM.format
        self.input_format.setPlaceholderText(msg)

    def connect_controls(self):
        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)

        self.layout_main.addWidget(self.input_format)
        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)
        self.input_format.returnPressed.connect(self.set_format)

    def refresh_active_token_widgets(self):
        for token, value in [(token, self.NOM.state[token.lower()]) for token in self.NOM.format_order]:
            token = token.lower()
            self.LOG.info('Running through token value pair %s:%s' % (token, value))
            token_widget = self.create_token_widget(token, value)
            receiversCount = token_widget.receivers(token_widget.changed)
            if receiversCount == 0:
                self.LOG.info('Connecting %s.changed -> %s.update_instance and adding to layout' % (token_widget, self))
                token_widget.changed.connect(self.update_instance)
                self.token_layout.addWidget(token_widget)

    def create_token_widget(self, token, value):
        token_widget = self.token_widget_lookup.get(token, None)
        if token_widget is None:
            self.LOG.debug('No preexisting token widget...creating and adding to %s.token_widget_lookup.' % self)
            token_widget = token_wgt.TokenWidget(token, value)
            self.token_widget_lookup[token] = token_widget
            self.add_token_widget_completion_from_config(token)
        else:
            self.token_layout.addWidget(token_widget)
        return token_widget

    def add_token_widget_completion_from_config(self, token):
        token_widget = self.token_widget_lookup.get(token, None)
        try:
            settings = [str(option) for option in self.NOM.cfg.get(token, list)]
            token_widget.value_widget.set_completer_items(settings)

        except nomenclate.core.errors.ResourceNotFoundError:
            self.LOG.debug('Could not find config entries for token %s' % token)

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
        try:
            self.NOM.format = input_format
        except nomenclate.core.errors.BalanceError as e:
            fix_msg = '\nYou need to fix it before you can input this format.'
            message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                                "Format Error",
                                                e.message + fix_msg,
                                                QtWidgets.QMessageBox.Ok, self)
            message_box.exec_()
        self.refresh()

    def refresh(self):
        self.clear_stale_token_widgets()
        self.refresh_active_token_widgets()
        self.update_instance("", "", "", "", "")

    def update_instance(self, token, value, capitalized='', prefix='', suffix=''):
        update_dict = {'token': token, 'value': value, 'capitalized': capitalized, 'prefix': prefix, 'suffix': suffix}
        self.LOG.info('Updating instance with %s' % update_dict)
        if any([token, capitalized, prefix, suffix]):
            self.NOM.merge_dict({token.encode('utf-8'): value.encode('utf-8')})
            token_attr = getattr(self.NOM, token)
            self.LOG.info('Obtained TokenAttr: %r, now modifying with new settings' % token_attr)
            token_attr.case_setting = capitalized
            token_attr.prefix_setting = prefix
            token_attr.suffix_setting = suffix
        self.nomenclate_output.emit(self.NOM.get())

    def set_output(self, input_name):
        self.output_name.setText(input_name)

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
