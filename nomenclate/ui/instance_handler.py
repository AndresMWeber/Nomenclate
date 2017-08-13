from six import iteritems
import Qt.QtCore as QtCore
import Qt.QtGui as QtGui
import Qt.QtWidgets as QtWidgets
import nomenclate
import nomenclate.settings as settings
import nomenclate.ui.utils as utils
import nomenclate.ui.components.format_widget as format_wgt
from nomenclate.ui.components.token_widget import TokenWidgetFactory
from nomenclate.ui.components.default import DefaultFrame

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class InstanceHandlerWidget(DefaultFrame):
    TITLE = 'File List View'
    TOKEN_COLORS = {}
    NOM = nomenclate.Nom()
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    nomenclate_output = QtCore.Signal(str)
    name_generated = QtCore.Signal(QtGui.QStandardItem, str)
    format_updated = QtCore.Signal(str, list, bool)
    token_colors_updated = QtCore.Signal(str, str, dict, list)

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)

        self.wgt_output = QtWidgets.QWidget()
        self.input_format = format_wgt.FormatWidget(starting_format=self.NOM.format)
        self.input_format_label = QtWidgets.QLabel('Naming Format: ')
        self.input_format_layout = QtWidgets.QHBoxLayout()

        self.output_layout = QtWidgets.QVBoxLayout(self.wgt_output)
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel(parent=self)

        self.token_frame = QtWidgets.QFrame(parent=self)
        self.token_layout = QtWidgets.QHBoxLayout(self.token_frame)

        self.token_widget_lookup = {}
        self.fold_state = True

    def initialize_controls(self):
        for layout in [self.output_layout, self.token_layout]:
            layout.setSpacing(0)
            layout.setContentsMargins(0, 0, 0, 0)

        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)

        self.layout_main.addLayout(self.input_format_layout)
        self.input_format_layout.addWidget(self.input_format_label, QtCore.Qt.AlignLeft)
        self.input_format_layout.addWidget(self.input_format, QtCore.Qt.AlignLeft)

        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)

        self.input_format_label.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Minimum)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.refresh_active_token_widgets()

        self.setObjectName('InstanceHandler')
        self.input_format_label.setObjectName('InputLabel')
        self.wgt_output.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')
        self.token_frame.setObjectName('SeeThrough')

        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.nomenclate_output.connect(self.output_name.setText)

        self.input_format.text_input.set_options(self.get_options_from_config('naming_formats', return_type=dict),
                                                 for_token=False)

    def connect_controls(self):
        self.input_format.format_updated.connect(self.set_format)
        self.input_format.escapePressed.connect(self.setFocus)
        self.format_updated.connect(self.generate_token_colors)
        self.format_updated.connect(lambda: self.fold(False))

        self.token_colors_updated.connect(self.color_token_widgets)
        self.token_colors_updated.connect(self.input_format.update_format_colors)
        self.format_updated.emit(self.NOM.format, self.NOM.format_order, True)

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

    def color_token_widgets(self, format_string, richtext_format_string, color_dict, swapped):
        # Need to ensure lower case tokens from the color dict since we lower cased in the TokenWidgets
        color_dict = {k.lower(): v for k, v in iteritems(color_dict)}
        for token_widget in self.active_token_widgets:
            token = token_widget.token.lower()

            if token in [str(color).lower() for color in list(color_dict)]:
                _, rich_color = color_dict.get(token)
                token_widget.set_category_title(token, rich_color)

    def generate_name(self, object_item, index, override_dict=None):
        """ Generates a name from the nomenclate instance for use in renaming.
        """
        if not override_dict:
            override_dict = self.default_override_incrementer(index)

        # Add all current values of the UI to the override dict to offset start values.
        for token, value in iteritems(override_dict):
            override_dict[token] = int((self.NOM.state.get(token, 0) or 0)) + int(value)

        name = self.NOM.get(**override_dict) if override_dict else self.NOM.get() + str(index)
        self.name_generated.emit(object_item, name)

    def default_override_incrementer(self, index):
        """ Finds the first incrementer (in order of appearance L->R) and uses that as the incrementer.

        :param index: int, given starting index.
        :return: dict, dictionary with override value
        """
        default_incr_tokens = ['version', 'var']
        for token in self.NOM.format_order:
            token_lower = token.lower()
            for default_incr_token in default_incr_tokens:
                if default_incr_token in token_lower:
                    return {token_lower: index + int(self.NOM.state.get(token_lower, 0) or 0)}
        return {}

    def fold(self, fold_override=None):
        """ alternates the state of all accordion widgets in the layout or overrides all using fold_override

        :param fold_override: bool, value to override as the fold state (true being folded)
        """
        self.fold_state = not self.fold_state if fold_override is None else fold_override
        for token_widget in self.active_token_widgets:
            token_widget.accordion_tree.fold(None, fold_override=self.fold_state)

    def get_options_from_config(self, search_path, return_type=list):
        """ Gets the token's options from the config for use as a auto completion in the token widget
        """
        try:
            return self.NOM.cfg.get(search_path, return_type)
        except nomenclate.core.errors.ResourceNotFoundError:
            self.LOG.debug('Could not find config entries for token %s' % search_path)

    def refresh_active_token_widgets(self):
        """ Makes sure all active token widgets are valid given the current naming format, adds new ones if missing
        """
        self.LOG.info('(refresh active token widgets) Current state and format order \n%s\n%s' % (self.NOM.state,
                                                                                                  self.NOM.format_order))
        for token, value in [(token, self.NOM.state[token.lower()]) for token in self.NOM.format_order]:
            token = token.lower()
            self.LOG.info('Running through token value pair %s:%s' % (token, value))
            token_widget = self.create_token_widget(token, value)
            self.LOG.info('Adding token_widget: %s to widget layout' % token_widget)
            self.token_layout.addWidget(token_widget)

    def create_token_widget(self, token, value):
        """ Creates appropriate token widget from the factory without conflicting current ones
            Finds the options from the config and
            Sets defaults.

        :param token:
        :param value:
        :return:
        """
        token_widget = self.token_widget_lookup.get(token, None)
        if token_widget is None:
            self.LOG.debug('No preexisting token widget...creating and adding to %s.token_widget_lookup.' % self)
            token_widget = TokenWidgetFactory.get_token_widget(token, value)
            token_widget.add_default_values_from_config(self.NOM.get_token_settings(token))
            token_widget.set_options(self.get_options_from_config(token, dict))
            token_widget.changed.connect(self.update_instance)
            self.token_widget_lookup[token] = token_widget

        else:
            self.token_layout.addWidget(token_widget)

        return token_widget

    def load_settings_from_config(self):
        """ Loads all settings from the config for all tokens widgets.
        """
        self.NOM.initialize_config_settings()
        for token, token_widget in iteritems(self.token_widget_lookup):
            token_widget.add_default_values_from_config(self.NOM.get_token_settings(token))

    def clear_stale_token_widgets(self):
        """ Removes unnecessary tokens if they aren't found in the current format string's order
        """
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

    def refresh(self):
        self.clear_stale_token_widgets()
        self.refresh_active_token_widgets()
        self.update_instance({})

    def update_instance(self, serialized_token_data):
        """ Updates the nomenclate instance based on the serialized token widget values/settings
        """

        token = str(serialized_token_data.pop('token', None))
        value = str(serialized_token_data.pop('value', None))

        self.LOG.debug('Updating instance with %s' % serialized_token_data)
        if value is not None and token is not None:
            self.NOM.merge_dict({token: value})

        if serialized_token_data:
            token_attr = getattr(self.NOM, token)

            for setting, value in iteritems(serialized_token_data):
                self.LOG.info('Obtained TokenAttr: %r, now modifying with new settings' % token_attr)
                set_on_object = token_attr if 'setting' in setting else self.NOM
                setattr(set_on_object, setting, value)

        self.LOG.debug('Updated Nomenclate state: %s\n%s' % (self.NOM.state, self.NOM.format))
        self.nomenclate_output.emit(self.NOM.get())

    def set_format(self):
        """ Sets the current nomenclate instance's format.
        """
        if self.input_format.text_utf:
            try:
                self.NOM.format = self.input_format.text_utf
                self.refresh()
                self.format_updated.emit(self.NOM.format, self.NOM.format_order, True)
            except nomenclate.core.errors.BalanceError as e:
                fix_msg = '\nYou need to fix it before you can input this format.'
                message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                                    "Format Error",
                                                    e.message + fix_msg,
                                                    QtWidgets.QMessageBox.Ok, self)
                message_box.exec_()

    def select_next_token_line_edit(self, direction):
        """ KeyPressEvent takeover to enable easy tabbing between token widget input lines
        """
        order = self.NOM.format_order
        direction_shifted_tokens = order[-1:] + order[:-1] if direction else order[1:] + order[:1]
        restart = order[-1] if direction else order[0]

        for token, next_token in zip(order, direction_shifted_tokens):
            token_widget = self.token_widget_lookup[token.lower()]
            if token_widget.is_selected() and restart != next_token:
                next_widget = self.token_widget_lookup[next_token.lower()]
                self.LOG.debug('Selecting from widget %r to next token widget (%s): %r' %
                               (token_widget, next_token, next_widget))
                try:
                    token_widget.value_widget.menu.close()
                except AttributeError:
                    pass

                next_widget.value_widget.setFocus()
                return True
        return False

    def generate_token_colors(self, richtext_format_string=None, format_order=None, swapped=False):
        """ Generates and emits a rich text string to update the tokens with.
        """
        dark = self.parent().dark.get()
        color_coded = self.parent().color_coded.get()
        richtext_format_string = richtext_format_string or self.NOM.format
        format_order = format_order or self.NOM.format_order
        original_format = richtext_format_string

        last_color = None

        for format_token in format_order:
            if color_coded:
                color, rich_color = None, None
                try:
                    color, rich_color = self.TOKEN_COLORS.get(format_token, None)
                except TypeError:
                    pass

                if color is None or rich_color is None or swapped:
                    color = self.get_safe_color(format_token, last_color, dark)
                    color = (min(abs(color[0]), 255), min(abs(color[1]), 255), min(abs(color[2]), 255))
                    rich_color = '<span style="color:{COLOR};">{TOKEN}</span>'.format(COLOR=utils.rgb_to_hex(color),
                                                                                      TOKEN=format_token)
            else:
                color = (0, 0, 0)
                rich_color = format_token

            self.TOKEN_COLORS[format_token] = (color, rich_color)
            last_color = color

        self.token_colors_updated.emit(original_format, richtext_format_string, self.TOKEN_COLORS, format_order)

    @staticmethod
    def get_safe_color(format_token, last_color, dark):
        """ Generates a safe color value from a persistent hash of the token string
            based on perceived contrast ratio against background.

        :param dark: bool, if we have a perceived dark background theme.
        :return:
        """
        color = None
        bg_score, color_score = 0, 0

        while bg_score < 8 and color_score < 3:
            nudge_value = 5 if dark else -5
            if color is None:
                color = utils.hex_to_rgb(utils.gen_color(utils.persistent_hash(format_token)))
            else:
                color = utils.nudge_color_value(utils.hex_to_rgb(color), nudge_value)
            contrast_against = (0, 0, 0) if dark else (1, 1, 1)
            bg_score = utils.get_contrast_ratio(color, contrast_against)
            if last_color:
                color_score = utils.get_contrast_ratio(color, last_color)

        return color
