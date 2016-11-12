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
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 2.0

import yaml
import os
import configparser
from collections import OrderedDict
import nomenclate.core.toolbox as tb
from copy import deepcopy

reload(tb)


class ConfigParse(object):
    SUPPORTED_CONFIGS = {'yml': 'yaml',
                         'ini': 'configparser',
                         'cfg': 'configparser'}

    def __init__(self, path=None):
        """
        Args:
            section (str): section to query
            subsection (str):subsection to query
        """
        if not path:
            path = tb.get_config_filepath()
        self.config_type = self.SUPPORTED_CONFIGS[self.valid_file(path)]
        self.path = path
        self.data = None
        self.rebuild_config_cache(self.path)

    @classmethod
    def valid_file(cls, config_file):
        if os.path.isfile(config_file):
            extsep = config_file.split(os.path.extsep)
            if len(extsep) > 1 and extsep[-1] in cls.SUPPORTED_CONFIGS.keys():
                return extsep[-1]
        raise IOError('File %s is not a valid yml, ini or cfg file' % config_file)

    def rebuild_config_cache(self, path):
        """ Loads from file and caches all data from the config file in the form of an OrderedDict to self.data
        Args:
            path (str): the full filepath to the config file
        Returns (bool): success status
        """
        data = None
        if self.config_type == 'configparser':
            parser = configparser.ConfigParser()
            parser.read(path)
            data = {s: dict(parser.items(s)) for s in parser.sections()}

        elif self.config_type == 'yaml':
            with open(self.path, 'r') as f:
                data = yaml.load(f)

        if data:
            self.data = self._dict_to_ordered_dict(data)
            return True
        return False

    def get_data(self, section="", subsection="", raw=False):
        self.query_valid_entry(section, subsection)
        if not subsection:
            query_result = self.data[section]
        else:
            query_result = self.data[section][subsection]
        # In this situation a user is looking for a string, let's give it to em!
        if raw:
            if isinstance(query_result, list):
                return ' '.join(query_result)
            elif isinstance(query_result, string_types):
                return query_result

        # Now we want just a normal list result
        if isinstance(query_result, string_types):
            return query_result.split(' ')
        return query_result

    def get(self, section=None, subsection=None, options=False, raw=False):
        """
        Args:
            section (str): section to query
            subsection (str): subsection to query
            options (bool): whether we want to just list the options for a section
            raw (bool): whether we want python formatted data or raw strings
        """
        if options:
            return self.list_section_options(section)
        return self.get_data(section, subsection, raw=raw)

    def query_valid_entry(self, section='', subsection=''):
        """ Function to check if the config section/subsection data exists
        """
        data_query = None
        if not subsection:
            data_query = self.data.get(section, '')
        else:
            data_query = self.data.get(section, {}).get(subsection, '')
        if not data_query:
            raise IOError('Section: %s and Subsection: %s not found in current config file...' % (section, subsection))
        return True

    def get_section(self, section=None, raw=False):
        """
        Returns (dict): dictionary of the entire contents of a specific section
        """
        return self.get(section, raw=raw)

    def get_subsection(self, section=None, subsection=None, raw=False):
        """ Return the given section/subsection pair as a list
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (dict): list of the subsection results
        """
        return self.get(section=section, subsection=subsection, raw=False)

    def get_subsection_as_dict(self, section=None, subsection=None):
        """ Return the given section/subsection pair as a dictionary
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (dict): dictionary of the subsection results
        """
        return {section: {subsection: self.get_subsection(section=section, subsection=subsection)}}

    def get_subsection_as_str(self, section=None, subsection=None):
        """ Return the given section/subsection pair as a string
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (str): string of the subsection results
        """
        return self.get(section=section, subsection=subsection, raw=True)

    def list_sections(self):
        """ Lists the sections possible to query
        Args (None)
        Returns [str]: list of section key names sorted by name so as not to mess with order.
        """
        keys = list(self.data.keys())
        keys.sort()
        return keys

    def list_section_options(self, section):
        """ Lists a section's possible options to query
        Args:
            section (str): section for us to query
        Returns [str]: list of string represented options
        """
        query_data = self.data[section]
        if isinstance(query_data, dict):
            return [k for k in self.data[section].keys()]
        elif isinstance(query_data, string_types):
            return query_data.split(' ')
        return query_data

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

    def __deepcopy__(self, memo):
        return self
