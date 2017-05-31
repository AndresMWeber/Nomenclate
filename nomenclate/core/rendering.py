#!/usr/bin/env python
from six import add_metaclass, iteritems
import re
import string
import datetime
import dateutil.parser as p
from . import errors as exceptions
import nomenclate.settings as settings
from .tools import (
    gen_dict_key_matches,
    flatten
)

MODULE_LOGGER_LEVEL_OVERRIDE = None


class TokenMatch(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def __init__(self, regex_match, substitution, group_name='token'):
        self.match = regex_match.group(group_name)
        self.start = regex_match.start(group_name)
        self.end = regex_match.end(group_name)
        self.sub = str(substitution)

    @property
    def span(self):
        return self.end - self.start

    def adjust_position(self, other, adjust_by_sub_delta=True):
        self._validate_adjuster(other)
        adjustment = other.span - len(other.sub) if adjust_by_sub_delta else other.span
        if adjustment:
            self.LOG.debug('Adjusting %s by %d' % (self, adjustment))
            self._adjust_order(adjustment)

    def _validate_adjuster(self, other):
        if not isinstance(other, self.__class__):
            raise IOError('Only TokenMatch objects are valid inputs to adjust_position')

        other.overlaps(self)

        if self < other:
            raise IndexError('Current TokenMatch is not affected by input TokenMatch\n\t%s\n\t%s' % (repr(self),
                                                                                                     repr(other)))

    def _adjust_order(self, adjust_value):
        self.start -= adjust_value
        self.end -= adjust_value
        self.LOG.debug('New positions are (%d-%d)' % (self.start, self.end))

    def overlaps(self, other):
        if self in other or other in self:
            raise exceptions.OverlapError('Match %s overlaps with an existing match:\n\t%s\n\t%s' % (self.match,
                                                                                                     self, other))
        return True

    def __contains__(self, other):
        try:
            return self.start < other.start < self.end or self.start < other.end < self.end
        except:
            raise NotImplementedError(
                '{C} objects do not handle in syntax for non class objects'.format(C=self.__class__.__name__))

    def __eq__(self, other):
        try:
            return (self.start == other.start and self.end == other.end and
                    self.match == other.match and self.sub == other.sub)
        except:
            raise NotImplementedError(
                '{C} objects do not handle == syntax for non class objects'.format(C=self.__class__.__name__))

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.end <= other.start
        else:
            raise NotImplementedError

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.start >= other.end
        else:
            raise NotImplementedError

    def __str__(self):
        return '%s (%d)- [%d:%d] - replacement = %s' % (self.match, self.span, self.start, self.end, self.sub)


class Nomenclative(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def __init__(self, input_str):
        self.str = input_str
        self.token_matches = []

    def process_matches(self):
        build_str = self.str
        for token_match in self.token_matches:
            if token_match.match == build_str[token_match.start:token_match.end]:
                self.LOG.debug('Processing: %s - %s - %s\n\t%s' % (token_match.match,
                                                                   token_match.sub,
                                                                   token_match.sub,
                                                                   build_str))

                build_str = build_str[:token_match.start] + token_match.sub + build_str[token_match.end:]
                self.adjust_other_matches(token_match)
                self.LOG.debug('Processed as:\n\t%s' % build_str)
        return build_str

    def adjust_other_matches(self, adjuster_match):
        for token_match in [token_match for token_match in self.token_matches if token_match != adjuster_match]:
            try:
                token_match.adjust_position(adjuster_match)
            except IndexError:
                pass
        adjuster_match.end = adjuster_match.start + len(adjuster_match.sub)
        adjuster_match.match = adjuster_match.sub

    def add_match(self, regex_match, substitution):
        token_match = TokenMatch(regex_match, substitution)
        try:
            self.validate_match(token_match)
            self.token_matches.append(token_match)
            self.LOG.info('Added match %s' % self.token_matches[-1])
        except IndexError:
            self.LOG.warning('Not adding match %s as it conflicts with a preexisting match' % token_match)

    def validate_match(self, token_match_candidate):
        for token_match in self.token_matches:
            try:
                token_match.overlaps(token_match_candidate)
            except exceptions.OverlapError as e:
                self.LOG.error(e.message)

    def __str__(self):
        matches = '' if not self.token_matches else '\n'.join(map(str, self.token_matches))
        return '%s:%s' % (self.str, matches)


class InputRenderer(type):
    RENDER_FUNCTIONS = {}
    REGEX_PARENTHESIS = r'([\(\)]+)'
    REGEX_BRACKETS = r'([\{\}]+)'
    REGEX_STATIC_TOKEN = r'(\(\w+\))'
    REGEX_BRACKET_TOKEN = r'(\{\w+\})'
    REGEX_TOKEN_SEARCH = r'(?P<token>((?<![a-z]){TOKEN}(?![0-9]))|((?<=[a-z]){TOKEN_CAPITALIZED}(?![0-9])))'

    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)
        token = dct.get('token', None)
        if token:
            mcs.RENDER_FUNCTIONS[token] = cls
        return cls

    @classmethod
    def render_unique_tokens(cls, nomenclate_object, input_dict):
        cls.LOG.info('current list of render functions: %s' % list(cls.RENDER_FUNCTIONS))
        for k, v in iteritems(input_dict):
            cls.LOG.info('Checking for unique token on token %s:%r' % (k, v))
            if v:
                # TODO: Split this into a separate validation function
                valid_functions = [func for func in list(cls.RENDER_FUNCTIONS)
                                   if k.replace(func, '').isdigit() or not k.replace(func, '')] or ['default']

                for func in valid_functions:
                    renderer = cls.RENDER_FUNCTIONS.get(func, None)
                    cls.LOG.info(
                        'Finding token specific render function for token %s with renderer %s' %
                        (k, renderer))

                    if func == 'default':
                        renderer.token = k

                    if 'render' in dir(renderer):
                        cls.LOG.info('render_unique_tokens() - Rendering token %r with %r, token settings=%s' %
                                     (k, v, nomenclate_object.get_token_settings(k)))

                        rendered_token = renderer.render(v, k, nomenclate_object,
                                                         **nomenclate_object.get_token_settings(k))
                        cls.LOG.info('Unique token %s rendered as: %s' % (k, rendered_token))

                        input_dict[k] = rendered_token

    @classmethod
    def render_nomenclative(cls, nomenclate_object):
        nomenclative = Nomenclative(nomenclate_object.format)
        token_values = nomenclate_object.token_dict.token_attr_dict
        cls.LOG.info('render_nomenclative() - Current state is %s with nomenclative %s' % (token_values, nomenclative))
        cls.render_unique_tokens(nomenclate_object, token_values)
        rendered_nomenclative = nomenclate_object.format
        cls.LOG.info('Finished rendering unique tokens.')
        cls._prepend_token_match_objects(token_values, rendered_nomenclative)

        for token, match_value in iteritems(token_values):
            nomenclative.add_match(*match_value)

        cls.LOG.info('Before processing state has been updated to %s' % nomenclative)
        rendered_nomenclative = cls.cleanup_formatted_string(nomenclative.process_matches())
        cls.LOG.info('Finally converted to %s' % rendered_nomenclative)
        return rendered_nomenclative

    @classmethod
    def _prepend_token_match_objects(cls, token_values, incomplete_nomenclative):
        for token, value in iteritems(token_values):
            re_token = cls.REGEX_TOKEN_SEARCH.format(TOKEN=token,
                                                     TOKEN_CAPITALIZED=token[0].upper() + token[1:])
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

    @staticmethod
    def _render_replacements(replacements_dict, incomplete_nomenclative):
        for token, match_value in iteritems(replacements_dict):
            match, value = match_value
            incomplete_nomenclative = incomplete_nomenclative.replace(match, value)

    @classmethod
    def cleanup_formatted_string(cls, formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores

        :param formatted_string: str, string that has had tokens replaced
        :return: str, cleaned up name of object
        """
        # TODO: chunk this out to sub-processes for easier error checking, could be own class
        # Remove whitespace
        result = formatted_string.replace(' ', '')
        # Remove any static token parentheses
        result = re.sub(cls.REGEX_PARENTHESIS, '', result)
        # Remove any multiple underscores
        result = re.sub('_+', '_', result)
        # Remove trailing or preceding non letter characters
        result = re.sub(r'(^[\W_]+)|([\W_]+$)', '', result)
        #  not sure what this one was...but certainly not it.
        result = re.sub(r'(\()|(\))', '', result)
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
        return [0, 'char_hi']


@add_metaclass(InputRenderer)
class RenderBase(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    token = 'default'

    @classmethod
    def render(cls, value, token, nomenclate_object, **kwargs):
        """ Default renderer for a token.  It checks the config for a match, if not found it uses the value provided.

        :param value: str, value we are trying to match (or config setting for the token)
        :param token: str, token we are searching for
        :param nomenclate_object: nomenclate.core.nomenclate.Nomenclate, instance of nomenclate object to query
        :param kwargs: any config settings that relate to the token as found from the nomenclate instance
        :return: str, the resulting syntactically rendered string
        """
        nomenclate_object.LOG.info('Attempting to default render %s with value %s and kwargs %s' % (token,
                                                                                                    value,
                                                                                                    kwargs))
        result = cls.get_config_match(value,
                                      cls.token,
                                      nomenclate_object.OPTIONS_PATH + [token],
                                      dict,
                                      nomenclate_object,
                                      **kwargs) or value

        return cls.handle_casing(result, kwargs.get('%s_case' % token))

    @staticmethod
    def handle_casing(value, case):
        if case == 'upper':
            value.upper()
        elif case == 'lower':
            value.lower()
        return value

    @classmethod
    def get_config_match(cls,
                         query_string,
                         token,
                         entry_path,
                         return_type,
                         nomenclate_object,
                         config_entry_suffix='length',
                         **kwargs):

        try:
            options = nomenclate_object.cfg.get(entry_path, return_type=return_type)

            if type(options) == dict:
                options = list(gen_dict_key_matches(query_string, options))
            options = list(flatten(options))

            criteria = kwargs.get('%s_%s' % (cls.token, config_entry_suffix), None)
            cls.LOG.info('%s(%s) options: %s criteria: %s' % (token, query_string, options, criteria))

            for option in options:
                cls.LOG.info('Running through option %s' % option)
                if len(option) == criteria and criteria:
                    cls.LOG.info('Found item matching criteria: %s -> %s' % (criteria, option))
                    return option

            try:
                result_option = next(options)
            except (StopIteration, TypeError):
                result_option = options

            cls.LOG.debug('Best match is: %s' % result_option)
            return result_option

        except exceptions.ResourceNotFoundError:
            cls.LOG.warning('No entry for token %s - defaulting to current: %s' % (token,
                                                                                   query_string))
            return query_string


class RenderDate(RenderBase):
    token = 'date'

    @classmethod
    def render(cls, date, token, nomenclate_object, **kwargs):
        if date == 'now':
            d = datetime.datetime.now()
        else:
            try:
                d = p.parse(date)
            except ValueError:
                return ''
        date_format = getattr(nomenclate_object, '%s_format' % cls.token, '%Y-%m-%d')
        # return d.strftime(get_keys_containing('format', nomenclate_object.__dict__, '%Y-%m-%d'))
        return d.strftime(date_format)


class RenderVar(RenderBase):
    token = 'var'

    @classmethod
    def render(cls, var, token, nomenclate_object, **kwargs):
        if var:
            var_index = kwargs.get('%s_index' % cls.token, 0)
            return cls._get_variation_id(var_index, var.isupper())
        else:
            return var

    @staticmethod
    def _get_variation_id(integer, capital=False):
        """ Convert an integer value to a character. a-z then double aa-zz etc
        Args:
            integer (int): integer index we're looking up
            capital (bool): whether we convert to capitals or not
        Returns (str): alphanumeric representation of the index
        """
        # calculate number of characters required
        base_power = base_start = base_end = 0
        while integer >= base_end:
            base_power += 1
            base_start = base_end
            base_end += pow(26, base_power)
        base_index = integer - base_start

        # create alpha representation
        alphas = ['a'] * base_power
        for index in range(base_power - 1, -1, -1):
            alphas[index] = chr(int(97 + (base_index % 26)))
            base_index /= 26

        characters = ''.join(alphas)
        return characters.upper() if capital else characters


class RenderVersion(RenderBase):
    token = 'version'

    @classmethod
    def render(cls, version, token, nomenclate_object, **kwargs):
        padding = kwargs.get('%s_padding' % token, 4)
        format = kwargs.get('%s_format' % token, '#')
        version_string = format.replace('#', '%0{0}d')
        return version_string.format(padding) % version


class RenderType(RenderBase):
    __metaclass__ = InputRenderer
    token = 'type'

    @classmethod
    def render(cls, engine_type, token, nomenclate_object, **kwargs):
        return cls.get_config_match(engine_type,
                                    cls.token,
                                    nomenclate_object.SUFFIXES_PATH,
                                    dict,
                                    nomenclate_object,
                                    **kwargs) or engine_type


class RenderSide(RenderBase):
    token = 'side'

    @classmethod
    def render(cls, side, token, nomenclate_object, **kwargs):
        return cls.get_config_match(side,
                                    cls.token,
                                    nomenclate_object.OPTIONS_PATH + [cls.token, side],
                                    list,
                                    nomenclate_object,
                                    **kwargs)


class RenderLocation(RenderBase):
    token = 'location'

    @classmethod
    def render(cls, location, token, nomenclate_object, **kwargs):
        return cls.get_config_match(location,
                                    cls.token,
                                    nomenclate_object.OPTIONS_PATH + [cls.token, location],
                                    list,
                                    nomenclate_object,
                                    **kwargs)


class RenderDiscipline(RenderBase):
    token = 'discipline'

    @classmethod
    def render(cls, discipline, token, nomenclate_object, **kwargs):
        return cls.get_config_match(discipline,
                                    cls.token,
                                    nomenclate_object.OPTIONS_PATH + [cls.token, discipline],
                                    list,
                                    nomenclate_object,
                                    **kwargs)
