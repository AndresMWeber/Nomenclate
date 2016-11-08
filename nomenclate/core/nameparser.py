#!/usr/bin/env python
"""
.. module:: nameparser
    :platform: N/A
    :synopsis: This module does name parsing to recover information about the name based on common conventions.
                it will be very prone to missing information since names will be very variable, but hopefully
                it will be more intelligent as time goes on.
    :plans: None
"""
import datetime
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = '0.1.0'


class NameParser(object):
    """ This parses names of assets.  It assumes the usual convention of strings separated by underscores.
    """
    @classmethod
    def short(cls, name):
        """ Returns the short name of a Maya asset name
        Args:
            name (str): string that represents a possible name of an object
        """
        return name.split('|')[-1]

    @classmethod
    def get_side(cls, name):
        """ Checks a string for a possible side string token
        Args:
            name (str): string that represents a possible name of an object
        """
        raise NotImplementedError

    @classmethod
    def get_base(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix)
        Args:
            name (str): string that represents a possible name of an object
        """
        raise NotImplementedError

    @classmethod
    def get_abbr(cls, name, lookup):
        """ Checks a string for a possible abbreviated form of the look up word
        Args:
            name (str): string that represents a possible name of an object
            lookup (str): full word that we want to look up
        """
        raise NotImplementedError

    @classmethod
    def get_date(cls, name):
        """ Checks a string for a possible date formatted into the name
            Args:
                name (str): string that represents a possible name of an object
        """
        raise NotImplementedError
