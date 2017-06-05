#!/usr/bin/env python
from six import add_metaclass, iteritems
import re
import string
import datetime
import dateutil.parser as p
from . import errors as exceptions
import nomenclate.settings as settings

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__

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
                '<%s>.__contains__ does not handle <%s>' % (self.__class__.__name__, type(other)))

    def __eq__(self, other):
        try:
            return (self.start == other.start and self.end == other.end and
                    self.match == other.match and self.sub == other.sub)
        except:
            raise NotImplementedError(
                '<%s>.__eq__ does not handle <%s>' % (self.__class__.__name__, type(other)))

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

    def __repr__(self):
        return '<%s %s (%d)- [%d:%d] - replacement = %s>' % (self.__class__.__name__,
                                                             self.match, self.span, self.start, self.end, self.sub)

    def __str__(self):
        return '%s:%s' % (self.match, self.sub)


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
        except (IndexError, exceptions.OverlapError):
            msg = 'Not adding match %s as it conflicts with a preexisting match' % token_match
            self.LOG.warning(msg)
            raise exceptions.OverlapError(msg)

    def validate_match(self, token_match_candidate):
        for token_match in self.token_matches:
            try:
                token_match.overlaps(token_match_candidate)
            except exceptions.OverlapError:
                msg = "Cannot add match %s due to overlap with %s" % (token_match, token_match_candidate)
                self.LOG.error(msg)
                raise exceptions.OverlapError(msg)

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
        cls.LOG.info('Current list of render functions: %s' % list(cls.RENDER_FUNCTIONS))
        cls.LOG.info('Checking against input dictionary %s' % input_dict)
        non_empty_token_entries = {_k: _v for _k, _v in iteritems(input_dict) if _v}

        for token, value in iteritems(non_empty_token_entries):
            cls.LOG.info('Checking for unique token on token %s:%r' % (token, value))
            for func in cls.get_valid_render_functions(token):
                renderer = cls.RENDER_FUNCTIONS.get(func, None)
                cls.LOG.info('Finding token specific render function for token %r with renderer %s' % (token, renderer))

                if func == 'default':
                    renderer.token = token

                if callable(getattr(renderer, 'render')):
                    cls.LOG.info('render_unique_tokens() - Rendering token %r: %r, token settings=%s' %
                                 (token, value, nomenclate_object.get_token_settings(token)))

                    rendered_token = renderer.render(value, token, nomenclate_object,
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
        cls.LOG.info('Found valid render functions for token %s: %s' % (token_name, render_functions))
        return render_functions or ['default']

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


@add_metaclass(InputRenderer)
class RenderBase(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    token = 'default'

    @classmethod
    def render(cls,
               value,
               token,
               nomenclate_object,
               config_query_path=None,
               return_type=list,
               use_value_in_query_path=True,
               **filter_kwargs):
        """ Default renderer for a token.  It checks the config for a match, if not found it uses the value provided.

        :param value: str, value we are trying to match (or config setting for the token)
        :param token: str, token we are searching for
        :param nomenclate_object: nomenclate.core.nomenclate.Nomenclate, instance of nomenclate object to query
        :param filter_kwargs: any config settings that relate to the token as found from the nomenclate instance
        :return: str, the resulting syntactically rendered string
        """
        if config_query_path == None:
            config_query_path = nomenclate_object.OPTIONS_PATH + [token]
            if use_value_in_query_path:
                config_query_path += [value]

        cls.LOG.info('Attempting to default render %s with value %s and kwargs %s' % (token, value, filter_kwargs))
        config_matches = cls.get_config_match(value,
                                              token,
                                              config_query_path,
                                              return_type,
                                              nomenclate_object,
                                              **filter_kwargs)

        options = cls.flatten_input(config_matches, value)
        option = cls.process_criteria(token, options, **filter_kwargs) if options else value
        return cls.process_token_augmentations(option, token_attr=getattr(nomenclate_object, token))

    @classmethod
    def process_token_augmentations(cls, value, token_attr):
        """ Uses any found augmentations from the TokenAttr to augment the final rendered value.  Currently
            this only processes the augmentations:
                TokenAttr().case
                TokenAttr().prefix
                TokenAttr().suffix

        :param value: str, the resulting rendered string from the TokenAttr
        :param token_attr: nomenclate.core.tokens.TokenAttr, the processed TokenAttr to be used to query settings.
        :return: str, final augmented string
        """
        cls.LOG.info('Processing augmentations for token attr %r and applying to value %r' % (token_attr, value))
        value = str(value)
        case_value = getattr(token_attr, 'case')

        value = getattr(value, case_value, str)() or value
        value = getattr(token_attr, 'prefix') + value
        value = value + getattr(token_attr, 'suffix')

        return value

    @classmethod
    def get_config_match(cls,
                         query_string,
                         token,
                         entry_path,
                         return_type,
                         nomenclate_object,
                         **filter_kwargs):
        """ Queries the nomenclate's config data for corresponding entries and filters against the incoming
            filter_kwargs as detailed in cls.process_criteria

        :param query_string: str, string to look for once we find a match in the config
        :param token: str, the given token to search for
        :param entry_path: list(str), the query path to the subsection we are looking for to get a match in the config
        :param return_type: type, the type of return value we want (usually should be <type str>)
        :param nomenclate_object: nomenclate.core.nomenclature.Nomenclate, instance to query against (has config data)
        :return: object, whatever return type was specified
        """
        try:
            return nomenclate_object.cfg.get(entry_path, return_type=return_type)
        except exceptions.ResourceNotFoundError:
            cls.LOG.warning('No entry for token %s - defaulting to current: %s' % (token, query_string))
            return query_string

    @classmethod
    def flatten_input(cls, options, query_string):
        """ Takes a list, dict or str of options and outputs a filtered list
            Behavior list:
                dict: flattens/filters the dict to only key matches based on query_string
                list: just flattens a list just in case it's nested.
                str: returns a list with the string in it

        :param options: list, dict, str, input options to flatten/filter
        :param query_string: str, string we are looking for if the input is a dictionary
        :return: list, flattened list.
        """
        cls.LOG.info('Flattening input %s for matches with %s' % (options, query_string))
        if not isinstance(options, (dict, list)):
            options = [options]
        else:
            if isinstance(options, dict):
                options = list(gen_dict_key_matches(query_string, options))

            options = list(flatten(options))
        cls.LOG.info('Flattened to %s' % options)
        return options

    @classmethod
    def process_criteria(cls, token, options, **filter_kwargs):
        """ Each kwarg passed is considered a filter.  The kwarg is in format <token>_<filter function> and if the
            filter function is found in __builtins__ it uses the filter function and checks the result against
            the kwarg's value.  If it passes the check it is filtered out of the current list of options

        :param token: str, token we are querying
        :param options: list(str), the options to filter with kwargs
        :param filter_kwargs: dict(str: str), dictionary of {<token>_<__builtin__ function>: compare value}
        :return:
        """
        options = [options] if isinstance(options, str) else options
        criteria_matches = list(options)
        print(options)

        for token_criteria, criteria_value in iteritems(filter_kwargs):
            builtin_func = token_criteria.replace('%s_' % token, '')
            try:
                builtin_func = getattr(__builtin__, builtin_func)
                cls.LOG.info('Filtering options: %s with criteria: %s' % (options, token_criteria))

                for option in options:
                    cls.LOG.info('Running through option %s' % option)
                    if token_criteria and criteria_value:
                        if not builtin_func(option) == criteria_value:
                            cls.LOG.info('Non criteria match for %s(%s)=%s' % (builtin_func, option, criteria_value))
                            criteria_matches.remove(option)
            except AttributeError:
                cls.LOG.warning('Criteria function %r is invalid...skipping' % builtin_func)
        cls.LOG.info('Found criteria matches: %s ...returning first' % criteria_matches)

        return criteria_matches[0]


class RenderDate(RenderBase):
    token = 'date'

    @classmethod
    def render(cls, date, token, nomenclate_object, **filter_kwargs):
        if date == 'now':
            d = datetime.datetime.now()
        else:
            try:
                d = p.parse(date)
            except ValueError:
                return ''
        date_format = getattr(nomenclate_object, '%s_format' % cls.token, '%Y-%m-%d')
        return d.strftime(date_format)


class RenderVar(RenderBase):
    token = 'var'

    @classmethod
    def render(cls, var, token, nomenclate_object, **filter_kwargs):
        if var:
            var_index = filter_kwargs.get('%s_index' % cls.token, 0)
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
    def render(cls, version, token, nomenclate_object, **filter_kwargs):
        padding = filter_kwargs.get('%s_padding' % token, 4)
        format = filter_kwargs.get('%s_format' % token, '#')
        version_string = format.replace('#', '%0{0}d')
        return version_string.format(padding) % version


class RenderType(RenderBase):
    __metaclass__ = InputRenderer
    token = 'type'

    @classmethod
    def render(cls, engine_type, token, nomenclate_object, **filter_kwargs):
        return super(RenderType, cls).render(engine_type,
                                             cls.token,
                                             nomenclate_object,
                                             config_query_path=nomenclate_object.SUFFIXES_PATH,
                                             return_type=dict,
                                             **filter_kwargs)
