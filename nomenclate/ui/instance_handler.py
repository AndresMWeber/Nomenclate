import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import nomenclate
import nomenclate.ui.utils as utils
import nomenclate.ui.token_widget as token_wgt
import nomenclate.ui.format_widget as format_wgt
import nomenclate.settings as settings
from default import DefaultWidget
import random
from six import iteritems

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class InstanceHandlerWidget(DefaultWidget):
    TITLE = 'File List View'
    TOKEN_COLORS = {}
    NOM = nomenclate.Nom()
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    nomenclate_output = QtCore.pyqtSignal(str)
    format_updated = QtCore.pyqtSignal(str, list, bool)
    token_colors_updated = QtCore.pyqtSignal(str, dict, list)

    def create_controls(self):
        self.layout_main = QtWidgets.QVBoxLayout(self)
        self.wgt_output = QtWidgets.QWidget()
        self.output_layout = QtWidgets.QVBoxLayout(self.wgt_output)
        self.output_title = QtWidgets.QLabel('Output Base Name')
        self.output_name = QtWidgets.QLabel()
        self.input_format = format_wgt.FormatWidget(starting_format=self.NOM.format)
        self.token_frame = QtWidgets.QFrame()
        self.token_layout = QtWidgets.QHBoxLayout(self.token_frame)
        self.token_layout.setContentsMargins(0, 0, 0, 0)
        self.token_layout.setSpacing(0)
        self.token_widget_lookup = {}
        self.fold_state = True

    def initialize_controls(self):
        self.output_layout.addWidget(self.output_title)
        self.output_layout.addWidget(self.output_name)
        self.layout_main.addWidget(self.input_format)
        self.layout_main.addWidget(self.token_frame)
        self.layout_main.addWidget(self.wgt_output)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.refresh_active_token_widgets()

        self.setObjectName('InstanceHandler')
        self.wgt_output.setObjectName('OutputWidget')
        self.output_title.setObjectName('OutputTitle')
        self.output_name.setObjectName('OutputLabel')
        self.nomenclate_output.connect(self.set_output)

        self.input_format.set_options(self.get_options_list('naming_formats', return_type=dict))

    def connect_controls(self):
        self.input_format.returnPressed.connect(self.set_format)
        self.format_updated.connect(self.generate_token_colors)

        self.token_colors_updated.connect(self.color_token_widgets)
        self.token_colors_updated.connect(self.input_format.update_format)

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

    def color_token_widgets(self, format_string, color_dict):
        # Need to ensure lower case tokens from the color dict since we lower cased in the TokenWidgets
        color_dict = {k.lower(): v for k, v in iteritems(color_dict)}
        for token_widget in self.active_token_widgets:
            token = token_widget.token.lower()

            if token in [str(color).lower() for color in list(color_dict)]:
                color, rich_color = color_dict.get(token)
                token_widget.set_category_title(token, rich_color)

    def get_index(self, index):
        return self.NOM.get() + str(index)

    def fold(self):
        self.fold_state = not self.fold_state
        for token_widget in self.active_token_widgets:
            token_widget.accordion_tree.fold(self.fold_state)

    def get_options_list(self, search_path, return_type=list):
        return self.NOM.cfg.get(search_path, return_type)

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
            options = self.get_completion_from_config(token)
            token_widget.value_widget.set_completer_items(options)
        else:
            self.token_layout.addWidget(token_widget)
        return token_widget

    def get_completion_from_config(self, search_string):
        try:
            return map(str, self.get_options_list(search_string, list))
        except nomenclate.core.errors.ResourceNotFoundError:
            self.LOG.debug('Could not find config entries for token %s' % search_string)

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
        try:
            self.NOM.format = self.input_format.text
            self.refresh()
            self.format_updated.emit(self.NOM.format, self.NOM.format_order, True)
        except nomenclate.core.errors.BalanceError as e:
            fix_msg = '\nYou need to fix it before you can input this format.'
            message_box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning,
                                                "Format Error",
                                                e.message + fix_msg,
                                                QtWidgets.QMessageBox.Ok, self)
            message_box.exec_()

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

    def generate_token_colors(self, format_string=None, format_order=None):
        dark = self.parent().dark

        format_string = format_string or self.NOM.format
        format_order = format_order or self.NOM.format_order

        last_color = None
        for format_token in format_order:
            if not self.TOKEN_COLORS.get(format_token):
                color = None
                bg_score, color_score = 0, 0

                while bg_score < 8 and color_score < 3:
                    nudge_value = 5 if dark else -5
                    if color is None:
                        color = utils.hex_to_rgb(utils.gen_color(hash(format_token)))
                        #print 'rand', color
                    else:
                        color = utils.nudge_color_value(utils.hex_to_rgb(color), nudge_value)
                        #print 'nudged', color
                    contrast_against = (0,0,0) if dark else (1,1,1)

                    bg_score = utils.get_contrast_ratio(color, contrast_against)
                    if last_color:
                        color_score = utils.get_contrast_ratio(color, last_color)
                print 'token %s ended on color %s with bg-contrast %f and color-contrast %f' % (format_token,
                                                                                                color,
                                                                                                bg_score,
                                                                                                color_score)
                rich_color = '<span style="color:{COLOR};">{TOKEN}</span>'.format(COLOR=utils.rgb_to_hex(color),
                                                                                  TOKEN=format_token)
                self.TOKEN_COLORS[format_token] = (color, rich_color)
                last_color = color

        self.token_colors_updated.emit(format_string, self.TOKEN_COLORS, format_order)
