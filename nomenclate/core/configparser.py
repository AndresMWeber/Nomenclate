#!/usr/bin/env python
"""
.. module:: configparser
    :platform: Ubuntu 16.04
    :synopsis: This module parses config files and retrieves data
    :plans: None
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.1

import ConfigParser
import os
from collections import OrderedDict
from copy import deepcopy


class ConfigParse(object):
    """
    testing:
        a = ConfigParse('D:\\Dropbox\\Dropbox\\_GIT\\Forge\\package\\env.ini')
        a.get_section('subset_formats')
        a.get_sections()
        a.get_section_options('naming_subsets')
        a.get('suffixes','mesh')
        a.get_subsection_as_list("naming_subsets", "subsets")
        a.get_subsection_as_dict("naming_subsets", "subsets")
        a.get_subsection_as_str("naming_subsets", "subsets")
    """

    def __init__(self, path, section="", subsection=""):
        """
        Args:
            section (str): section to query
            subsection (str):subsection to query
        """
        self.path = path
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(self.path)
        self.section = section
        self.subsection = subsection

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
        if self.exists():
            return self.get_data(raw=raw)

    def exists(self):
        """ Function to check if the config section/subsection data exists
        """
        if not os.path.exists(self.path):
            raise IOError("Cannot find ini file %s" % self.path)
        try:
            self.parser.get(self.section, self.subsection)
            return True
        except:
            print "Section %s and subsection %s do not exist" % (self.section, self.subsection)

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
