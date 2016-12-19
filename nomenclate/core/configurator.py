# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems

"""
.. module:: configurator
    :platform: Win/Linux/Mac
    :synopsis: This module parses config files and retrieves data
    :plans: Support beyond 1 level nesting and customization apart from my current setup
    :changelog:
        2.0 - Added YAML support
"""

import yaml
import os
from collections import OrderedDict
import nomenclate.core.toolbox as tb
import nomenclate.core.exceptions as exceptions

class ConfigParse(object):
    def __init__(self, config_filepath=None):
        """
        Args:
            section (str): section to query
            subsection (str):subsection to query
        """
        if not config_filepath:
            config_filepath = tb.get_config_filepath()
        self.path = config_filepath
        self.config_file_contents = None
        self.config_entry_handler = ConfigEntryFormatter()
        self.rebuild_config_cache(self.path)

    def rebuild_config_cache(self, config_filepath):
        """ Loads from file and caches all data from the config file in the form of an OrderedDict to self.data
        Args:
            config_filepath (str): the full filepath to the config file
        Returns (bool): success status
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
        self.path = config_filepath

    def get(self, query_path, default=None, return_type=list, preceding_depth=None):
        """ Traverses the list of query paths to find the data requested
        Args:
            query_path list(str)]: list of query path branches
            return_type (Union[list, str, dict, OrderedDict]): desired return type for the data
            preceding_depth (int): always returns a dictionary encapsulating the data
                                    that traces back up the path for x depth
                                    -1 for the full traversal back up the path
                                    None is default for no traversal
        """
        query_path = query_path if isinstance(query_path, list) else [query_path]
        self.validate_query_path(query_path)
        config_entry = self.get_path_entry_from_config(query_path)
        query_result = self.config_entry_handler.format_query_result(config_entry,
                                                                     query_path,
                                                                     return_type,
                                                                     preceding_depth)
        return query_result

    def get_path_entry_from_config(self, query_path):
        if not query_path:
            return list(self.config_file_contents)
        cur_data = self.config_file_contents
        for child in query_path:
            cur_data = cur_data.get(child)
        return cur_data

    @classmethod
    def validate_config_file(cls, config_filepath):
        if not os.path.isfile(config_filepath):
            raise IOError('File %s is not a valid yml, ini or cfg file or does not exist' % config_filepath)

        elif os.path.getsize(config_filepath) == 0:
            raise IOError('File %s is empty' % config_filepath)

        with open(config_filepath, 'r') as f:
            if yaml.load(f) is None:
                raise IOError('No YAML config was found in file %s' % config_filepath)

    def validate_query_path(self, query_path):
        """ Determines whether the query path given is found in the current dataset
        Args:
            query_path list(str): list of query paths to traverse
        Returns (bool): True or raise IndexError on non found query
        """
        cur_data = self.config_file_contents
        for path in query_path:
            cur_data = cur_data.get(path)
            if cur_data is None:
                raise exceptions.ResourceNotFoundError(
                    'Trying to find entry: %s not found in current config file...' % ('|'.join(query_path)))


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


class BaseFormatter(object):
    __metaclass__ = FormatterRegistry
    converts = {'accepted_input_type': None,
                'accepted_return_type': None}

    def __init__(self, parent):
        self.parent = parent

    @staticmethod
    def format_result(input):
        raise NotImplementedError


class StringToListEntryFormatter(BaseFormatter):
    converts = {'accepted_input_type': str,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        return input.split()


class DictToStringEntryFormatter(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': str}

    @staticmethod
    def format_result(input):
        return ' '.join(list(input))


class DictToListEntryFormatter(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': list}

    @staticmethod
    def format_result(input):
        """ Always sorted for order
        """
        keys = list(input)
        keys.sort()
        return keys


class DictToOrderedDictEntryFormatter(BaseFormatter):
    converts = {'accepted_input_type': dict,
                'accepted_return_type': OrderedDict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        try:
            items = list(iteritems(input))
        except AttributeError:
            items = list(input.items())
        return OrderedDict(sorted(items, key=lambda x: x[0]))


class ListToStringEntryFormatter(BaseFormatter):
    converts = {'accepted_input_type': list,
                'accepted_return_type': str}

    @staticmethod
    def format_result(input):
        return ' '.join(input)


class ConfigEntryFormatter(object):
    def format_query_result(self, query_result, query_path, return_type=list, preceding_depth=None):
        """
        Args:
            query_result (dict|str|list): yaml query result
            query_path [str]: list of strings representing query path
            return_type (rtype): return type of object user desires
            preceding_depth (int): the depth to which we want to encapsulate back up config tree
                                    -1 : defaults to entire tree
        Returns (dict|OrderedDict|str|list): specified return type
        """
        if type(query_result) != return_type:
            converted_result = self.format_with_handler(query_result, return_type)
        else:
            converted_result = query_result

        converted_result = self.add_preceding_dict(converted_result, query_path, preceding_depth)
        return converted_result

    def get_handler(self, query_result_type, return_type):
        try:
            return FormatterRegistry.get_by_take_and_return_type(query_result_type, return_type)
        except AttributeError:
            raise AttributeError(
                "Handler not found for return type %s and input type %s" % (return_type, type(query_result_type)))
        except:
            raise IndexError('Could not find function in conversion list',
                             'for input type %s and return type %s' % (query_result_type, return_type))

    def format_with_handler(self, query_result, return_type):
        handler = self.get_handler(type(query_result), return_type)
        return handler.format_result(query_result)

    def add_preceding_dict(self, config_entry, query_path, preceding_depth):
        if preceding_depth is None:
            return config_entry

        preceding_dict = {query_path[-1]: config_entry}
        path_length_minus_query_pos = len(query_path) - 1
        preceding_depth = path_length_minus_query_pos - preceding_depth if preceding_depth != -1 else 0

        for index in reversed(range(preceding_depth, path_length_minus_query_pos)):
            preceding_dict = {query_path[index]: preceding_dict}

        return preceding_dict
