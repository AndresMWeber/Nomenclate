from six import iteritems
import hashlib
import os
import operator
import random
import Qt.QtCore as QtCore
import Qt.QtWidgets as QtWidgets
import Qt.QtGui as QtGui
import nomenclate

APPLICATIONS = ['Maya', 'Nuke', 'Python']

ALPHANUMERIC_VALIDATOR = QtCore.QRegExp('[A-Za-z0-9_]*')
TOKEN_VALUE_VALIDATOR = QtCore.QRegExp('^(?!^_)(?!.*__+|\.\.+.*)[a-zA-Z0-9_\.]+(?!_)$')
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resource')
FONTS_PATH = os.path.join(RESOURCES_PATH, 'fonts')

REGISTERED_INCREMENTER_TOKENS = ['var', 'version']

SETTER = 'SET'
GETTER = 'GET'

OBJECT_PATH_SEPARATOR = '|'

ICON_FILE = 'file'
ICON_FOLDER = 'folder'
ICON_OBJECT = 'object'
ICON_TAG = 'tag'
ICON_SAVE = 'save'

ICON_SET = {
    ICON_FILE: 'document.png',
    ICON_FOLDER: 'folder.png',
    ICON_OBJECT: 'object.png',
    ICON_TAG: 'tag.png',
    ICON_SAVE: 'floppy-disc.png'
}

INPUT_WIDGETS = {
    QtWidgets.QComboBox: {GETTER: QtWidgets.QComboBox.currentIndex,
                          SETTER: QtWidgets.QComboBox.setCurrentIndex},

    QtWidgets.QLineEdit: {GETTER: QtWidgets.QLineEdit.text,
                          SETTER: QtWidgets.QLineEdit.setText},

    QtWidgets.QCheckBox: {GETTER: QtWidgets.QCheckBox.checkState,
                          SETTER: QtWidgets.QCheckBox.setCheckState},

    QtWidgets.QSpinBox: {GETTER: QtWidgets.QSpinBox.value,
                         SETTER: QtWidgets.QSpinBox.setValue},

    QtWidgets.QTimeEdit: {GETTER: QtWidgets.QTimeEdit.setTime,
                          SETTER: QtWidgets.QTimeEdit.time},

    QtWidgets.QDateEdit: {GETTER: QtWidgets.QDateEdit.date,
                          SETTER: QtWidgets.QDateEdit.setDate},

    QtWidgets.QDateTimeEdit: {GETTER: QtWidgets.QDateTimeEdit.dateTime,
                              SETTER: QtWidgets.QDateTimeEdit.setDateTime},

    QtWidgets.QRadioButton: {GETTER: QtWidgets.QRadioButton.isChecked,
                             SETTER: QtWidgets.QRadioButton.checkStateSet},

    QtWidgets.QSlider: {GETTER: QtWidgets.QSlider.value,
                        SETTER: QtWidgets.QSlider.setValue},
}


def get_application_type():
    application = QtWidgets.QApplication.instance()
    environment_application = application.applicationName()
    for supported_application in APPLICATIONS:
        if supported_application in environment_application:
            return supported_application
    return None


def get_icon(icon_name):
    return QtGui.QIcon(os.path.join(RESOURCES_PATH, 'icons', ICON_SET.get(icon_name)))


def cache_function(func):
    func.cacheable = True
    return func


class Cacheable(object):
    __CACHE__ = {}

    def cache_method(self, func):
        def wrapper(*args, **kw):
            name = "%s%r%r" % (func.__name__, args, kw)
            if name not in self.__CACHE__:
                self.__CACHE__[name] = func(*args, **kw)

            return self.__CACHE__[name]

        wrapper.__name__ = func.__name__

        return wrapper

    def __getattribute__(self, attr):
        function = super(Cacheable, self).__getattribute__(attr)

        if attr != 'cache_method' and callable(function) and hasattr(function, 'cacheable'):
            return self.cache_method(function)

        return function


def get_all_widget_children(widget, children=None):
    if children is None:
        children = []
    children.append(widget)

    if widget.children():
        for child in widget.children():
            get_all_widget_children(child, children)
    return children


def give_children_unique_names(widget):
    for index, child_widget in enumerate(get_all_widget_children(widget)):
        for input_widget_type in list(INPUT_WIDGETS):
            if issubclass(type(child_widget), input_widget_type):
                widget_title = getattr(widget, 'category_title', '')
                child_name = '%sChild%s%d' % (widget.__class__.__name__, widget_title, index)
                child_widget.setObjectName(child_name)


def walk_search(text, start_position, match_list, direction='backward'):
    end_pos = 0 if direction == 'backward' else len(text) - 1
    text_slice = text[start_position:] if direction == 'forward' else reversed(text[0:start_position])

    for index, char in enumerate(text_slice):
        dir_op_a = operator.add
        if direction == 'backward':
            index += 1
            dir_op_a = operator.sub

        abs_index = dir_op_a(start_position, index)
        at_end = abs_index == end_pos
        if char in match_list or at_end:
            adjusted_end_index = index + 1 if direction == 'forward' else index
            adjusted_mid_index = index if direction == 'forward' else index - 1
            index = adjusted_end_index if at_end else adjusted_mid_index
            return dir_op_a(start_position, index)


def find_whole_word_span(text, position=0):
    start = walk_search(text, position, nomenclate.settings.SEPARATORS, direction='backward')
    end = walk_search(text, position, nomenclate.settings.SEPARATORS, direction='forward')
    return (start, end)


def find_whole_word(text, position=0):
    start, end = find_whole_word_span(text, position)
    return text[start:end]


def replace_str_absolute(text, replacement, start, end=None):
    output_text = list(text)
    replacement_index = 0

    if end is None:
        end = start + len(replacement) - 1

    if end > len(text) - 1:
        output_text += [' '] * (end - len(text) + 1)

    replace_char = ' '
    for index, _ in enumerate(output_text):
        if end >= index >= start:
            try:
                replace_char = replacement[replacement_index]
            except IndexError:
                pass
            output_text[index] = replace_char
            replacement_index += 1
    return ''.join([_ for _ in output_text if _ != ' '])


def gen_color(seed=None):
    if seed is not None:
        random.seed(seed - 8)
    r = lambda: random.randint(0, 255)
    return '#%02X%02X%02X' % (r(), r(), r())


def hex_to_rgb(hex_color):
    if isinstance(hex_color, str):
        hex_color = hex_color.replace('#', '')
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    else:
        return hex_color


def rgb_to_hex(rgb_color):
    return '#%02x%02x%02x' % (rgb_color[0], rgb_color[1], rgb_color[2])


def get_contrast_YIQ(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    yiq = ((r * 299) + (g * 587) + (b * 114)) / 1000  # 'black' if yiq >= 128 else 'white'
    return yiq


def get_luminance(color_code):
    index = float(color_code) / 255
    if index < 0.03928:
        return index / 12.92
    else:
        return ((index + 0.055) / 1.055) ** 2.4


def get_relative_luminance(rgb):
    r, g, b = rgb
    r_lum, g_lum, b_lum = get_luminance(r), get_luminance(g), get_luminance(b)
    return 0.2126 * r_lum + 0.7152 * g_lum + 0.0722 * b_lum


def get_contrast_ratio(color_a, color_b, mode=0):
    """
    (ratio 0-3) incidental usage or logotypes."
    (ratio 3-4.5) minimum contrast large text."
    (ratio 4.5-7) minimum contrast or enhanced contrast large text."
    (ratio >= 7) enhanced contrast."
    """
    light = color_a if sum(color_a) > sum(color_b) else color_b
    dark = color_a if sum(color_a) < sum(color_b) else color_b
    contrast_ratio = (get_relative_luminance(light) + 0.05) / (get_relative_luminance(dark) + 0.05)
    if mode:
        yiq_contrast_ratio = (get_contrast_YIQ(light) / (get_contrast_YIQ(dark) or 0.01))
        contrast_ratio = yiq_contrast_ratio

    return contrast_ratio


def nudge_color_value(rgb_color, nudge_val):
    return [color + nudge_val for color in rgb_color]


def convert_config_lookup_to_options(config_lookup, result=None, parent=None, index=None):
    if result is None:
        result = []
    if isinstance(config_lookup, (list, tuple)):
        convert_config_lookup_to_options(parent, result)
    elif isinstance(config_lookup, dict):
        for key, value in iteritems(config_lookup):
            convert_config_lookup_to_options(value, result, parent=key, index=None)
    else:
        result.append(config_lookup)
    return result


def persistent_hash(string_input):
    return int(hashlib.md5(str(string_input).encode('utf-8')).hexdigest(), 16)
