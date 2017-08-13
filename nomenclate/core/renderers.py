#!/usr/bin/env python
from six import add_metaclass, iteritems, moves
import datetime
import dateutil.parser as p
import nomenclate.settings as settings
from . import rendering
from . import errors as exceptions
from .tools import (
    gen_dict_key_matches,
    flatten
)

MODULE_LOGGER_LEVEL_OVERRIDE = None


@add_metaclass(rendering.InputRenderer)
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
        options = list(options)
        criteria_matches = list(options)

        for criteria_function_name, criteria in iteritems(filter_kwargs):
            if not criteria_function_name and not criteria:
                continue
            criteria_function_name = criteria_function_name.replace('%s_' % token, '')

            try:
                builtin_func = getattr(moves.builtins, criteria_function_name)
                cls.LOG.info('Filtering options: %s with criteria: %s' % (options, criteria_function_name))
                criteria_matches = [option for option in options if builtin_func(option) == criteria]
            except AttributeError:
                cls.LOG.warning('Criteria function %r is invalid...skipping' % criteria_function_name)

            if not criteria_matches:
                criteria_matches = [min(options, key=lambda x: abs(builtin_func(x) - criteria))]
        cls.LOG.info('Found criteria matches: %s ...returning first' % criteria_matches)
        return criteria_matches[0] if criteria_matches else options[0]


class RenderDate(RenderBase):
    token = 'date'

    @classmethod
    def render(cls,
               date,
               token,
               nomenclate_object,
               config_query_path=None,
               return_type=list,
               use_value_in_query_path=True,
               **filter_kwargs):
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
    def render(cls,
               var,
               token,
               nomenclate_object,
               config_query_path=None,
               return_type=list,
               use_value_in_query_path=True,
               **filter_kwargs):
        var_format = filter_kwargs.get('%s_format' % cls.token, 'A')
        var = cls._get_variation_id(var, var_format.isupper())
        return cls.process_token_augmentations(var, token_attr=getattr(nomenclate_object, token))

    @staticmethod
    def _get_variation_id(value, capital=False):
        """ Convert an integer value to a character. a-z then double aa-zz etc
        Args:
            value (int): integer index we're looking up
            capital (bool): whether we convert to capitals or not
        Returns (str): alphanumeric representation of the index
        """
        # Reinforcing type just in case a valid string was entered
        value = int(value)
        base_power = base_start = base_end = 0
        while value >= base_end:
            base_power += 1
            base_start = base_end
            base_end += pow(26, base_power)
        base_index = value - base_start

        # create alpha representation
        alphas = ['a'] * base_power
        for index in range(base_power - 1, -1, -1):
            alphas[index] = chr(int(97 + (base_index % 26)))
            base_index /= 26

        characters = ''.join(alphas)
        return characters.upper() if capital else characters


class RenderLod(RenderVar):
    token = 'lod'


class RenderVersion(RenderBase):
    token = 'version'

    @classmethod
    def render(cls,
               version,
               token,
               nomenclate_object,
               config_query_path=None,
               return_type=list,
               use_value_in_query_path=True,
               **filter_kwargs):
        padding = filter_kwargs.get('%s_padding' % token, 4)
        token_format = filter_kwargs.get('%s_format' % token, '#')
        version_string = token_format.replace('#', '%0{0}d')
        version = version_string.format(padding) % int(version)
        return cls.process_token_augmentations(version, token_attr=getattr(nomenclate_object, token))


class RenderType(RenderBase):
    token = 'type'

    @classmethod
    def render(cls,
               engine_type,
               token,
               nomenclate_object,
               config_query_path=None,
               return_type=list,
               use_value_in_query_path=True,
               **filter_kwargs):
        return super(RenderType, cls).render(engine_type,
                                             cls.token,
                                             nomenclate_object,
                                             config_query_path=nomenclate_object.SUFFIXES_PATH,
                                             return_type=dict,
                                             **filter_kwargs)
