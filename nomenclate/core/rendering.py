#!/usr/bin/env python
from six import iteritems
from collections import Counter
import re
import string
import nomenclate.settings as settings
from . import processing

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class InputRenderer(type):
    RENDER_FUNCTIONS = {}

    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)
        token = dct.get('token', None)
        if token:
            mcs.RENDER_FUNCTIONS[token] = cls
        return cls

    @classmethod
    def render_unique_tokens(cls, nomenclate_object, input_dict):
        cls.LOG.info('Current list of render functions: %s' % list(cls.RENDER_FUNCTIONS))
        cls.LOG.info('Checking against input dictionary %s' % input_dict)
        non_empty_token_entries = {_k: _v for _k, _v in iteritems(input_dict) if not _v == ''}

        for token, value in iteritems(non_empty_token_entries):
            cls.LOG.info('Checking for unique token on token %s:%r' % (token, value))
            for func in cls.get_valid_render_functions(token):
                cls.LOG.info(
                    'Finding render function for token %s in functions: %s' % (func, list(cls.RENDER_FUNCTIONS)))
                renderer = cls.RENDER_FUNCTIONS.get(func, None)
                if func == 'default':
                    renderer.token = token
                cls.LOG.info('Finding token specific render function for token %r with renderer %s' % (token, renderer))

                if callable(getattr(renderer, 'render')):
                    cls.LOG.info('render_unique_tokens() - Rendering token %r: %r, token settings=%s' %
                                 (token, value, nomenclate_object.get_token_settings(token)))

                    rendered_token = renderer.render(value,
                                                     token,
                                                     nomenclate_object,
                                                     **nomenclate_object.get_token_settings(token))
                    cls.LOG.info('Unique token %s rendered as: %s' % (token, rendered_token))

                    input_dict[token] = rendered_token

    @classmethod
    def get_valid_render_functions(cls, token_name):
        render_functions = []
        for func in list(cls.RENDER_FUNCTIONS):
            is_sub_token = token_name.replace(func, '').isdigit()
            is_token_renderer = not token_name.replace(func, '')
            if is_sub_token or is_token_renderer:
                render_functions.append(func)
        render_functions = render_functions or ['default']
        cls.LOG.info('Found valid render functions for token %s: %s' % (token_name, render_functions))
        return render_functions

    @classmethod
    def render_nomenclative(cls, nomenclate_object):
        nomenclative = processing.Nomenclative(nomenclate_object.format)
        token_values = nomenclate_object.token_dict.token_attr_dict
        cls.LOG.info('render_nomenclative() - Current state is %s with nomenclative %s' % (token_values, nomenclative))
        cls.render_unique_tokens(nomenclate_object, token_values)
        rendered_nomenclative = nomenclate_object.format
        cls.LOG.info('Finished rendering unique tokens.')
        cls._prepend_token_match_objects(token_values, rendered_nomenclative)

        for token, match_value in iteritems(token_values):
            nomenclative.add_match(*match_value)

        cls.LOG.info('Before processing state has been updated to:\n%s' % nomenclative)
        rendered_nomenclative = cls.cleanup_formatted_string(nomenclative.process_matches())
        cls.LOG.info('Finally converted to %s' % rendered_nomenclative)
        return rendered_nomenclative

    @classmethod
    def _prepend_token_match_objects(cls, token_values, incomplete_nomenclative):
        for token, value in iteritems(token_values):
            regex_token = token.replace('(', '\(').replace(')', '\)')
            re_token = settings.REGEX_TOKEN_SEARCH.format(TOKEN=regex_token,
                                                          TOKEN_CAPITALIZED=regex_token.capitalize())
            cls.LOG.info('Searching through string %s for token %s with regex %s' % (incomplete_nomenclative,
                                                                                     token,
                                                                                     re_token))
            re_matches = re.finditer(re_token, incomplete_nomenclative, 0)

            for re_match in re_matches:
                token_values[token] = (re_match, value)

        cls._clear_non_matches(token_values)

    @staticmethod
    def _clear_non_matches(token_values):
        to_delete = []
        for token, value in iteritems(token_values):
            if isinstance(value, str) or not isinstance(value, tuple):
                to_delete.append(token)

        for delete in to_delete:
            token_values.pop(delete)

    @classmethod
    def cleanup_formatted_string(cls, formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores

        :param formatted_string: str, string that has had tokens replaced
        :return: str, cleaned up name of object
        """
        # Remove whitespace
        result = formatted_string.replace(' ', '')
        cls.LOG.debug('Removed whitespace, now %s' % result)
        # Remove any static token parentheses
        result = re.sub(settings.REGEX_PARENTHESIS, '', result)
        cls.LOG.debug('Removed parenthesis around static tokens, now %s' % result)
        # Remove any multiple separator characters
        multi_character_matches = re.finditer('[%s]{2,}' % settings.SEPARATORS, result)
        for multi_character_match in sorted(multi_character_matches, key=lambda x: len(x.group()), reverse=True):
            match = multi_character_match.group()
            most_common_separator = Counter(list(multi_character_match.group())).most_common(1)[0][0]
            result = result.replace(match, most_common_separator)
        cls.LOG.debug('Removed multi-line characters, now %s' % result)
        # Remove trailing or preceding non letter characters
        result = re.sub(settings.REGEX_ADJACENT_UNDERSCORE, '', result)
        cls.LOG.debug('leading/trailing underscore characters, now %s' % result)
        #  not sure what this one was...but certainly not it.
        result = re.sub(settings.REGEX_SINGLE_PARENTHESIS, '', result)
        cls.LOG.debug('single parenthesis characters, now %s' % result)
        return result

    @staticmethod
    def _get_alphanumeric_index(query_string):
        """ Given an input string of either int or char, returns what index in the alphabet and case it is

        :param query_string: str, query string
        :return: (int, str), list of the index and type
        """
        # TODO: could probably rework this. it works, but it's ugly as hell.
        try:
            return [int(query_string), 'int']
        except ValueError:
            if len(query_string) == 1:
                if query_string.isupper():
                    return [string.ascii_uppercase.index(query_string), 'char_hi']
                elif query_string.islower():
                    return [string.ascii_lowercase.index(query_string), 'char_lo']
            else:
                raise IOError('The input is a string longer than one character')
