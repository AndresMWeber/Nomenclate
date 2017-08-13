from six import iteritems
from collections import OrderedDict
from six import add_metaclass
from pprint import pformat
import yaml
import os

import nomenclate.settings as settings
from . import errors as errors
from .tools import (
    gen_dict_key_matches
)

MODULE_LOGGER_LEVEL_OVERRIDE = None


class ConfigEntryFormatter(object):
    def format_query_result(self, query_result, query_path, return_type=list, preceding_depth=None):
        """ Formats the query result based on the return type requested.

        :param query_result: (dict or str or list), yaml query result
        :param query_path: (str, list(str)), representing query path
        :param return_type: type, return type of object user desires
        :param preceding_depth: int, the depth to which we want to encapsulate back up config tree
                                    -1 : defaults to entire tree
        :return: (dict, OrderedDict, str, list), specified return type
        """
        if type(query_result) != return_type:
            converted_result = self.format_with_handler(query_result, return_type)
        else:
            converted_result = query_result

        converted_result = self.add_preceding_dict(converted_result, query_path, preceding_depth)
        return converted_result

    def format_with_handler(self, query_result, return_type):
        """ Uses the callable handler to format the query result to the desired return type

        :param query_result: the result value of our query
        :param return_type: desired return type
        :return: type, the query value as the return type requested
        """
        handler = self.get_handler(type(query_result), return_type)
        return handler.format_result(query_result)

    @staticmethod
    def get_handler(query_result_type, return_type):
        """ Find the appropriate return type handler to convert the query result to the desired return type

        :param query_result_type: type, desired return type
        :param return_type: type, actual return type
        :return: callable, function that will handle the conversion
        """
        try:
            return FormatterRegistry.get_by_take_and_return_type(query_result_type, return_type)
        except (IndexError, AttributeError, KeyError):
            msg = 'Could not find function in conversion list for input type %s and return type %s' % \
                  (query_result_type, return_type)
            raise IndexError(msg)

    @staticmethod
    def add_preceding_dict(config_entry, query_path, preceding_depth):
        """ Adds the preceeding config keys to the config_entry to simulate the original full path to the config entry

        :param config_entry: object, the entry that was requested and returned from the config
        :param query_path: (str, list(str)), the original path to the config_entry
        :param preceding_depth: int, the depth to which we are recreating the preceding config keys
        :return: dict, simulated config to n * preceding_depth
        """
        if preceding_depth is None:
            return config_entry

        preceding_dict = {query_path[-1]: config_entry}
        path_length_minus_query_pos = len(query_path) - 1
        preceding_depth = path_length_minus_query_pos - preceding_depth if preceding_depth != -1 else 0

        for index in reversed(range(preceding_depth, path_length_minus_query_pos)):
            preceding_dict = {query_path[index]: preceding_dict}

        return preceding_dict


class ConfigParse(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    config_entry_handler = ConfigEntryFormatter()

    def __init__(self, config_filepath='env.yml'):
        """

        :param config_filepath: str, the path to a user specified config, or the nomenclate default
        """
        self.config_filepath = self.resolve_config_file_path(config_filepath)
        self.config_file_contents = None
        self.rebuild_config_cache(self.config_filepath)

    def resolve_config_file_path(self, config_filepath):
        """ Determines whether given path is valid, and if so uses it.
            Otherwise searches both the working directory and nomenclate/core for the specified config file.

        :param config_filepath: str, file path or relative file name within package
        :return: str, resolved full file path to the config file
        """
        search_paths = [config_filepath,
                        os.path.normpath(os.path.join(os.getcwd(), config_filepath)),
                        os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), config_filepath))]

        for search_path in search_paths:
            try:
                self.LOG.info('Checking for config file at path %s' % search_path)
                self.validate_config_file(search_path)
                self.LOG.info('File %s is valid.  Returning.' % config_filepath)
                return search_path
            except (IOError, OSError):
                pass

        msg = 'No config file found in current working directory or nomenclate/core and %s is not a valid YAML file'
        self.LOG.warning(msg)
        raise errors.SourceError(msg)

    def rebuild_config_cache(self, config_filepath):
        """ Loads from file and caches all data from the config file in the form of an OrderedDict to self.data

        :param config_filepath: str, the full filepath to the config file
        :return: bool, success status
        """
        self.validate_config_file(config_filepath)
        config_data = None
        try:
            with open(config_filepath, 'r') as f:
                config_data = yaml.load(f)
            items = list(iteritems(config_data))

        except AttributeError:
            items = list(config_data)

        self.config_file_contents = OrderedDict(sorted(items, key=lambda x: x[0], reverse=True))
        self.config_filepath = config_filepath

    def get(self, query_path=None, return_type=list, preceding_depth=None, throw_null_return_error=False):
        """ Traverses the list of query paths to find the data requested

        :param query_path: (list(str), str), list of query path branches or query string
                                             Default behavior: returns list(str) of possible config headers
        :param return_type: (list, str, dict, OrderedDict), desired return type for the data
        :param preceding_depth: int, returns a dictionary containing the data that traces back up the path for x depth
                                     -1: for the full traversal back up the path
                                     None: is default for no traversal
        :param throw_null_return_error: bool, whether or not to throw an error if we get an empty result but no error
        :return: (list, str, dict, OrderedDict), the type specified from return_type
        :raises: exceptions.ResourceNotFoundError: if the query path is invalid
        """
        function_type_lookup = {str: self._get_path_entry_from_string,
                                list: self._get_path_entry_from_list}

        self.LOG.info(
            'config.get() - Trying to find %s in config and return_type %s' % (repr(query_path), return_type))

        if query_path is None:
            return self._default_config(return_type)

        try:
            config_entry = function_type_lookup.get(type(query_path), str)(query_path)
            self.LOG.info('Retrieved config entry:\n%s' % pformat(config_entry, depth=1))
            query_result = self.config_entry_handler.format_query_result(config_entry,
                                                                         query_path,
                                                                         return_type=return_type,
                                                                         preceding_depth=preceding_depth)
            self.LOG.info('Converted config entry:\n%s' % pformat(query_result, depth=1))

            return query_result
        except IndexError:
            self.LOG.info('IndexError was found...defaulting to return: %s = %r' %
                          (return_type, return_type()))
            return return_type()

    def _get_path_entry_from_string(self, query_string, first_found=True, full_path=False):
        """ Parses a string to form a list of strings that represents a possible config entry header

        :param query_string: str, query string we are looking for
        :param first_found: bool, return first found entry or entire list
        :param full_path: bool, whether to return each entry with their corresponding config entry path
        :return: (Generator((list, str, dict, OrderedDict)), config entries that match the query string
        :raises: exceptions.ResourceNotFoundError
        """
        iter_matches = gen_dict_key_matches(query_string, self.config_file_contents, full_path=full_path)
        try:
            return next(iter_matches) if first_found else iter_matches
        except (StopIteration, TypeError):
            raise errors.ResourceNotFoundError('Could not find search string %s in the config file contents %s' %
                                               (query_string, self.config_file_contents))

    def _get_path_entry_from_list(self, query_path):
        """ Returns the config entry at query path

        :param query_path: list(str), config header path to follow for entry
        :return: (list, str, dict, OrderedDict), config entry requested
        :raises: exceptions.ResourceNotFoundError
        """
        cur_data = self.config_file_contents
        try:
            self.LOG.info('starting path search from list...' % query_path)
            for child in query_path:
                self.LOG.debug(' -> %s' % child)
                cur_data = cur_data[child]
            self.LOG.debug('Found data %s' % cur_data)
            return cur_data
        except (AttributeError, KeyError):
            raise errors.ResourceNotFoundError('Could not find query path %s in the config file contents' %
                                               query_path)

    def _default_config(self, return_type):
        """ Generates a default instance of whatever the type requested was (in case of miss)

        :param return_type: type, type of object requested
        :return: object, instance of return_type
        """
        self.LOG.debug('Returning default for type %s -> %s' % (return_type, repr(return_type())))
        if return_type == list:
            return [k for k in self.config_file_contents]
        return return_type()

    @classmethod
    def validate_config_file(cls, config_filepath):
        """ Validates the filepath to the config.  Detects whether it is a true YAML file + existance

        :param config_filepath: str, file path to the config file to query
        :return: None
        :raises: IOError
        """
        is_file = os.path.isfile(config_filepath)
        if not is_file and os.path.isabs(config_filepath):
            raise IOError('File path %s is not a valid yml, ini or cfg file or does not exist' % config_filepath)

        elif is_file:
            if os.path.getsize(config_filepath) == 0:
                raise IOError('File %s is empty' % config_filepath)

        with open(config_filepath, 'r') as f:
            if yaml.load(f) is None:
                raise IOError('No YAML config was found in file %s' % config_filepath)


class FormatterRegistry(type):
    CONVERSION_TABLE = {}

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)

        extensions = dct.get('converts')
        accepted_input_type = extensions.get('accepted_input_type', None)
        accepted_return_type = extensions.get('accepted_return_type', None)

        if accepted_input_type and accepted_return_type:
            take_exists = mcs.CONVERSION_TABLE.get(accepted_input_type)
            if not take_exists:
                mcs.CONVERSION_TABLE[accepted_input_type] = {}

            mcs.CONVERSION_TABLE[accepted_input_type][accepted_return_type] = cls

        return cls

    @classmethod
    def get_by_take_and_return_type(mcs, input_type, return_type):
        return mcs.CONVERSION_TABLE[input_type][return_type]


@add_metaclass(FormatterRegistry)
class BaseFormatter(object):
    converts = {'accepted_input_type': None,
                'accepted_return_type': None}

    @staticmethod
    def format_result(input):
        raise NotImplementedError


class StringToList(BaseFormatter):
    converts = {'accepted_input_type': str,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        return input.split()


class DictToString(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': str}

    @staticmethod
    def format_result(input):
        return ' '.join(list(input))


class DictToList(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        """ Always sorted for order
        """
        keys = list(input)
        keys.sort()
        return keys


class DictToOrderedDict(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': OrderedDict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        items = list(iteritems(input))
        return OrderedDict(sorted(items, key=lambda x: x[0]))


class OrderedDictToList(BaseFormatter):
    converts = {'accepted_input_type': OrderedDict,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        return list(input)


class NoneToDict(BaseFormatter):
    converts = {'accepted_input_type': type(None),
                'accepted_return_type': dict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        return {}


class ListToString(BaseFormatter):
    converts = {'accepted_input_type': list,
                'accepted_return_type': str}

    @staticmethod
    def format_result(input):
        return ' '.join(input)


class IntToList(BaseFormatter):
    converts = {'accepted_input_type': int,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        return [input]
