# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from builtins import dict
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
    SUPPORTED_CONFIGS = {'yml': 'yaml'}

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
        self.config_entry_handler = ConfigEntryHandler()
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

    def get(self, query_path, default=None, return_type=dict, preceding_depth=-1):
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
        """
        self.validate_query_path(query_path)
        config_entry = self.get_path_entry_from_config(query_path)
        query_result = self.config_entry_handler.format_query_result(config_entry, query_path, return_type, preceding_depth)

    def get_path_entry_from_config(self, query_path):
        cur_data = self.data
        for child in query_path:
            cur_data = cur_data.get(child)
        return cur_data

    @classmethod
    def validate_file(cls, config_file):
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


class BaseDelegate(object):
    converts = {'takes':None,
                'returns':None}

    def __init__(self, parent):
        self.parent=parent

    def format_result(self, input):
        raise NotImplementedError


class StringToListEntryFormatter(BaseDelegate):
    converts = {'takes': str,
                'returns': list}

    def format_result(self, input):
         pass


class DictToStringEntryFormatter(BaseDelegate):
    handles_type = {'takes': dict,
                    'returns': list}

    def format_result(self, input):
        return ' '.join(list(input))


class DictToListEntryFormatter(BaseDelegate):
    handles_type = {'takes': dict,
                    'returns': list}

    def format_result(self, input):
         pass


class DictToOrderedDictEntryFormatter(BaseDelegate):
    handles_type = {'takes': dict,
                    'returns': OrderedDict}

    def format_result(self, input):
         pass


class ListToStringEntryFormatter(BaseDelegate):
    handles_type = {'takes': list,
                    'returns': str}

    def format_result(self, input):
        return ' '.join(input)

class ListToDictEntryFormatter(BaseDelegate):
    handles_type = {'takes': list,
                    'returns': dict}

    def format_result(self, input):
         pass

class ConfigEntryHandler(object):
    def __init__(self):
        self.entry_formatters = [
            StringToListEntryFormatter(self),
            DictToOrderedDictEntryFormatter(self),
            ListToStringEntryFormatter(self),
            ListToDictEntryFormatter(self)
        ]

    def format_query_result(self, value, query_path, return_type, preceding_depth):
        """
        Args:
            value:
            query_path:
            return_type (str): return type of object user desires
            preceding_depth (int): the depth to which we want to encapsulate back up config tree
                                    -1 : defaults to entire tree
        Returns (dict|OrderedDict|str|list): specified return type
        """
        converted_result = self.get_handler(value, return_type).format_result(value)
        self.to_dict_preceeding(converted_result, preceding_depth)

    def get_handler(self, input, return_type):
        for entry_formatter in self.entry_formatters:
            if (entry_formatter.handles_type['takes'] == type(input) and
                        entry_formatter.handles_type['takes'] == return_type):
                return entry_formatter
        raise TypeError('Entry type %s or requested type %s was not found in the handler list' % (type(input), return_type))

    def add_preceeding_dict(self, config_entry):
        pass



    def _to_string(self, input):
        """ Helper function that converts found data to strings depending on input type
        """
        if isinstance(input, list):
        elif isinstance(input, dict):
        elif isinstance(input, string_types):
            return input
        else:
            raise IndexError('The requested data (%s) was not a list or string.' % input)

    def _to_dict(self, input, query_path, as_ordered_dict=False, as_sub_dict=False):
        """ Helper function that converts found data to 3 types of dictionaries depending on input type
        """
        buffer = {query_path[-1]: input}

        if not as_sub_dict:
            for path in query_path[0:-1][::-1]:
                buffer = {path: buffer}

        elif as_sub_dict:
            if isinstance(input, dict):
                buffer = input

        return buffer if not as_ordered_dict else self._dict_to_ordered_dict(buffer)

    def list_headers(self):
        """ Lists the sections possible to query
        Args (None)
        Returns [str]: list of section key names sorted by name so as not to mess with order.
        """
        keys = list(self.data.keys())
        keys.sort()
        return keys

    def list_section_options(self, query_path):
        """ Lists a section's possible options to query
        Args:
            section (str): section for us to query
        Returns [str]: list of string represented options
        """
        query_data = self.get(query_path)

        if isinstance(query_data, dict):
            return list(query_data)

        elif isinstance(query_data, string_types):
            return query_data.split(' ')

        elif isinstance(query_data, list):
            return query_data

        raise IOError("The requested subsection was not a dict, str or list, sorry!")

    @staticmethod
    def _dict_to_ordered_dict(d):
        """ Private function for converting to ordered dictionary
            From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        Args:
            d (dictionary): unsorted dictionary
        Returns (OrderedDictionary): dictionary in order...
        """
        try:
            items = list(d.iteritems())
        except AttributeError:
            items = list(d.items())
        return OrderedDict(sorted(items, key=lambda x: x[0], reverse=True))