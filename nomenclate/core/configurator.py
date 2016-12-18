# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload
from six import string_types
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



class ConfigParse(object):
    def __init__(self, path=None):
        """
        Args:
            section (str): section to query
            subsection (str):subsection to query
        """
        if not path:
            path = tb.get_config_filepath()
        self.path = path
        self.data = None
        self.config_entry_handler = ConfigEntryFormatter()
        self.rebuild_config_cache(self.path)

    def rebuild_config_cache(self, path):
        """ Loads from file and caches all data from the config file in the form of an OrderedDict to self.data
        Args:
            path (str): the full filepath to the config file
        Returns (bool): success status
        """
        data = None
        try:
            with open(path, 'r') as f:
                data = yaml.load(f)
            items = list(data.iteritems())

        except IOError:
            raise IOError('Could not find file %s in the local directories' % path)

        except AttributeError:
            items = list(d.items())

        self.data = OrderedDict(sorted(items, key=lambda x: x[0], reverse=True))
        self.path = path

    def get(self, query_path, default=None, return_type=dict, preceding_depth=None):
        """ Traverses the list of query paths to find the data requested
        Args:
            query_path [str]: list of query path branches
            return_type (str): desired return type for the data:
                                list
                                str
                                dict
                                OrderedDict
            preceding_depth (int): always returns a dictionary encapsulating the data
                                    that traces back up the path for x depth
                                    -1 for the full traversal back up the path
                                    None is default for no traversal
        """
        query_path = query_path if isinstance(query_path, list) else [query_path]
        self.validate_query_path(query_path)
        config_entry = self.get_path_entry_from_config(query_path)
        query_result = self.config_entry_handler.format_query_result(config_entry, query_path, return_type, preceding_depth)
        return query_result

    def get_path_entry_from_config(self, query_path):
        if not query_path:
            return list(self.data)
        cur_data = self.data
        for child in query_path:
            cur_data = cur_data.get(child)
        return cur_data

    @classmethod
    def validate_config_file(cls, config_file):
        if not os.path.isfile(config_file):
            raise IOError('File %s is not a valid yml, ini or cfg file or does not exist' % config_file)

        elif os.stat(config_file).st_size > 0:
            raise IOError('File %s is empty' % config_file)

        with open(config_file, 'r') as f:
            if yaml.load(f) is None:
                raise IOError('No YAML config was found in file %s' % config_file)

    def validate_query_path(self, query_path):
        """ Determines whether the query path given is found in the current dataset
        Args:
            query_path [str]: list of query paths to traverse
        Returns (bool): True or raise IndexError on non found query
        """
        cur_data = self.data
        for path in query_path:
            cur_data = cur_data.get(path)
            if cur_data is None:
                raise IndexError('Trying to find entry: %s not found in current config file...' % ('|'.join(query_path)))


class FormatterRegistry(type):
    CONVERSION_TABLE = {}
    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)

        extensions = dct.get('converts')
        takes = extensions.get('takes', None)
        returns = extensions.get('returns', None)

        if takes and returns:
            mcs.CONVERSION_TABLE[takes] = dict(mcs.CONVERSION_TABLE.get(takes, {}), **{returns: cls})

        return cls

    @classmethod
    def get_by_take_and_return_type(mcs, input_type, return_type):
        return mcs.CONVERSION_TABLE.get(input_type).get(return_type)


class BaseFormatter(object):
    __metaclass__ = FormatterRegistry
    converts = {'takes':None,
                'returns':None}

    def __init__(self, parent):
        self.parent=parent

    @staticmethod
    def format_result(input):
        raise NotImplementedError


class StringToListEntryFormatter(BaseFormatter):
    converts = {'takes': str,
                'returns': list}

    @staticmethod
    def format_result(input):
         return input.split()


class DictToStringEntryFormatter(BaseFormatter):
    converts = {'takes': dict,
                'returns': str}

    @staticmethod
    def format_result(input):
        return ' '.join(list(input))


class DictToListEntryFormatter(BaseFormatter):
    converts = {'takes': dict,
                'returns': list}

    @staticmethod
    def format_result(input):
        """ Always sorted for order
        """
        keys = list(input)
        keys.sort()
        return keys


class DictToOrderedDictEntryFormatter(BaseFormatter):
    converts = {'takes': dict,
                'returns': OrderedDict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        try:
            items = list(input.iteritems())
        except AttributeError:
            items = list(input.items())
        return OrderedDict(sorted(items, key=lambda x: x[0]))


class ListToStringEntryFormatter(BaseFormatter):
    converts = {'takes': list,
                'returns': str}

    @staticmethod
    def format_result(input):
        return ' '.join(input)


class ConfigEntryFormatter(object):
    def format_query_result(self, query_result, query_path, return_type=dict, preceding_depth=None):
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
            converted_result = self.get_handler(type(query_result), return_type).format_result(query_result)
        else:
            converted_result = query_result

        if preceding_depth is not None:
            converted_result = self.add_preceding_dict(converted_result, query_path, preceding_depth)
        return converted_result

    def get_handler(self, input_type, return_type):
        try:
            return FormatterRegistry.get_by_take_and_return_type(input_type, return_type)
        except:
            raise IndexError('Could not find function in conversion list',
                             'for input type %s and return type %s' % (input_type, return_type))

    def add_preceding_dict(self, config_entry, query_path, preceding_depth):
        preceding_dict = {query_path[-1]: config_entry}
        path_length_minus_query_pos = len(query_path) - 1
        preceding_depth = path_length_minus_query_pos - preceding_depth if preceding_depth != -1 else 0

        for index in reversed(range(preceding_depth, path_length_minus_query_pos)):
            preceding_dict = {query_path[index]: preceding_dict}

        return preceding_dict
