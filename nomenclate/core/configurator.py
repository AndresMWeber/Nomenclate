# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload
"""
.. module:: configurator
    :platform: Win/Linux/Mac
    :synopsis: This module parses config files and retrieves data
    :plans: Change this to YAML, more powerful and better for nested things etc
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.1


import os
import configparser
from collections import OrderedDict
import nomenclate.core.toolbox as tb
from copy import deepcopy

reload(tb)

class ConfigParse(object):
    """ A class for retrieving config information for the system
    """
    def __init__(self, path=None, section="", subsection=""):
        """
        Args:
            section (str): section to query
            subsection (str):subsection to query
        """
        self.path = path
        if not path:
            self.path = tb.get_config_filepath()
        self.parser = configparser.ConfigParser()
        self.section = section
        self.subsection = subsection

        self.load_config(self.path)

    def load_config(self, path):
        if os.path.isfile(path):
            self.path=path
            self.parser.read(self.path)
        else:
            IOError('Input config file not found: %s' % path)

    def get_data(self, raw=False):
        return self.parser.get(self.section, self.subsection, raw=raw)

    def get(self, section=None, subsection=None, options=False, raw=False):
        """ general getter, specify subsection and section, or get all possible sections with options flag true
        Args:
            section (str): section to query for
            subsection (str): subsection to query for
            options (bool): whether to just return the possible options (subsections) or not
            raw (bool): whether to return a raw result or not
        """
        self.section = section or self.section
        self.subsection = subsection or self.subsection
        if options:
            return self.parser.options(self.section)
        if self.query_valid_entry(self.section, self.subsection):
            return self.get_data(raw=raw)

    def query_valid_entry(self, section, subsection):
        """ Function to check if the config section/subsection data exists
        """
        try:
            self.parser.get(section, subsection)
            return True
        except (configparser.NoOptionError, configparser.NoSectionError):
            raise IOError("Section %s and subsection %s do not exist" % (self.section, self.subsection))

    def get_section(self, section=None, raw=False):
        """ Getter for a specific subsection, will return as a dictionary all possible options in the section
        Args:
            section (str): section to query
            raw (bool): whether to get raw results or not
        Returns dict: resulting subsection and all of its entries
        """
        result = OrderedDict()
        self.section = section or self.section
        subsections = self.get(options=True)
        for subsection in subsections:
            result[subsection] = self.get(section=section, subsection=subsection, raw=raw)
        return result

    def get_subsection_as_dict(self, section=None, subsection=None):
        """ Return the given section/subsection pair as a dictionary
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (dict): dictionary of the subsection results
        """
        data = self.get(section=section, subsection=subsection)
        return {section: {subsection: self.parser.get(section, subsection, raw=True).split(' ')}}

    def get_subsection_as_list(self, section=None, subsection=None):
        """ Return the given section/subsection pair as a list
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (dict): list of the subsection results
        """
        return self.get(section=section, subsection=subsection, raw=True).split(' ')

    def get_subsection_as_str(self, section=None, subsection=None):
        """ Return the given section/subsection pair as a string
        Args:
            section (str): section to query
            subsection (str): subsection to query
        Returns (str): string of the subsection results
        """
        return self.get(section=section, subsection=subsection)

    def get_sections(self):
        """ Return all sections of the config file
        Returns (list): list of sections
        """
        return self.parser.sections()

    def get_section_options(self, section):
        """ Gets all the options for a given section
        Args:
            section (str): section to query
        """
        section = section or self.section
        return self.parser.options(section)

    def __deepcopy__(self, memo):
        return self
