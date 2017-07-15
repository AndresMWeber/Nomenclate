import PyQt5.QtCore as QtCore
import os
import operator
import nomenclate
import random

ALPHANUMERIC_VALIDATOR = QtCore.QRegExp('[A-Za-z0-9_]*')
TOKEN_VALUE_VALIDATOR = QtCore.QRegExp('^(?!^_)(?!.*__+|\.\.+.*)[a-zA-Z0-9_\.]+(?!_)$')
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resource')
FONTS_PATH = os.path.join(RESOURCES_PATH, 'fonts')


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


def walk_search(text, start_position, match_list, direction='backward'):
    end_pos = 0 if direction == 'backward' else len(text) - 1
    slice = text[start_position:] if direction == 'forward' else reversed(text[0:start_position])

    for index, char in enumerate(slice):
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
    for index, char in enumerate(output_text):
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
        random.seed(seed)
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
    light = color_a if sum(color_a) > sum(color_b) else color_b
    dark = color_a if sum(color_a) < sum(color_b) else color_b

    contrast_ratio = (get_relative_luminance(light) + 0.05) / (get_relative_luminance(dark) + 0.05)

    if mode:
        yiq_contrast_ratio = (get_contrast_YIQ(light) / (get_contrast_YIQ(dark) or 0.01))
        contrast_ratio = yiq_contrast_ratio

    if contrast_ratio < 3:
        usable_for = "(ratio 0-3) incidental usage or logotypes."
    elif contrast_ratio >= 3 and contrast_ratio < 4.5:
        usable_for = "(ratio 3-4.5) minimum contrast large text."
    elif contrast_ratio >= 4.5 and contrast_ratio < 7:
        usable_for = "(ratio 4.5-7) minimum contrast or enhanced contrast large text."
    elif contrast_ratio >= 7:
        usable_for = "(ratio >= 7) enhanced contrast."
    """
    print(str("Contrast ratio calculator\n"
              "Usable for the W3C Web Content Accessibility Guidelines (WCAG) 2.0\n"
              "http://www.w3.org/TR/2008/REC-WCAG20-20081211/\n"
              "1.4.3 Contrast (Minimum): 4.5:1 (Large text: 3:1)\n"
              "1.4.6 Contrast (Enhanced): 7:1 (Large text: 4.5:1)\n"
              "Calculated contrast:\n"
              "{:.01F}:1 Usable for {}\n").format(contrast_ratio, usable_for))
    """
    return contrast_ratio


def nudge_color_value(rgb_color, nudge_val):
    return [color + nudge_val for color in rgb_color]
