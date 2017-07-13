import PyQt5.QtCore as QtCore
import os
import operator
import nomenclate

ALPHANUMERIC_VALIDATOR = QtCore.QRegExp('[A-Za-z0-9_]*')
TOKEN_VALUE_VALIDATOR = QtCore.QRegExp('^(?!^_)(?!.*__+|\.\.+.*)[a-zA-Z0-9_\.]+(?!_)$')
RESOURCES_PATH = os.path.join(os.path.dirname(__file__), 'resource')
FONTS_PATH = os.path.join(RESOURCES_PATH, 'fonts')


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
        output_text += [' '] * (end - len(text)+1)

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
