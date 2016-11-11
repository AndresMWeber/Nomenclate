#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
from imp import reload
"""
.. module:: nameparser
    :platform: Win/Linux/Mac
    :synopsis: This module does name parsing to recover information about the name based on common conventions.
                it will be very prone to missing information since names will be very variable, but hopefully
                it will be more intelligent as time goes on.
    :plans:
        0.1.0: Added base template functionality
        0.2.0: Added abbreviation generation technology
        0.2.1: Removed nomenclate.core.toolbox opting to auto-configure config path
               Optimized get_side to use the env.ini settings
"""
import re
import datetime
import itertools
import nomenclate.core.configurator as config

__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = '0.3.0'

reload(config)

class NameParser(object):
    """ This parses names of assets.  It assumes the usual convention of strings separated by underscores.
    """
    @classmethod
    def get_short(cls, name):
        """ Returns the short name of a Maya asset name
        Args:
            name (str): string that represents a possible name of an object
        """
        return name.split('|')[-1]

    @classmethod
    def get_side(cls, name):
        """ Checks a string for a possible side string token, this assumes its on its own
            and is not part of or camel cased and combined with a word.  Returns first found side to reduce duplicates.
            We can be safe to assume the abbreviation for the side does not have camel casing within its own word.
        Args:
            name (str): string that represents a possible name of an object
        """
        sides = config.ConfigParse().get_subsection_as_list(section='options', subsection='side')
        for side in sides:
            # Have to check for longest first and remove duplicates
            abbreviations = list(set([i for i in cls._get_abbrs(side)]))
            abbreviations.sort()
            abbreviations.reverse()
            for abbr in abbreviations:
                # We won't check for abbreviations that are stupid eg something with apparent camel casing within
                # the word itself like LeF
                for permutation in cls._get_casing_permutations(abbr):
                    if not cls._valid_camel(permutation):
                        continue
                    separators = r'[ ,_\-!?:]'
                    abbr_island = r'[{SEP}]+({ABBR})[{SEP}]+'
                    abbr_seos = r'(?:^|[A-Z]|{SEP})({ABBR})(?:$|[A-Z]|{SEP})'
                    abbr_camel = r'(?:[a-z])({ABBR})(?:$|[A-Z]|{SEP})'

                    patterns = [abbr_seos.format(ABBR=permutation, SEP=separators),
                                abbr_island.format(ABBR=permutation, SEP=separators)]

                    # One check for camel casing exception case
                    if permutation[0].isupper():
                        patterns.insert(0, abbr_camel.format(ABBR=permutation, SEP=separators))

                    for pattern in patterns:
                        matches = [match for match in re.findall(pattern, name)]
                        if matches:
                            return [side, permutation]
        return None

    @classmethod
    def get_base(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix)
        Args:
            name (str): string that represents a possible name of an object
        """
        raise NotImplementedError

    @classmethod
    def get_date(cls, name):
        """ Checks a string for a possible date formatted into the name.  It assumes dates do not have other
            numbers at the front or head of the date.  Heavily relies on datetime for error checking to see
            if date is actually viable. It follows similar ideas to this post:
            http://stackoverflow.com/questions/9978534/match-dates-using-python-regular-expressions
            Args:
                name (str): string that represents a possible name of an object
            Returns (datetime.datetime): datetime object with current time or None if not found
        """
        time_formats = ['%Y-%m-%d_%H-%M-%S',
                        '%Y-%m-%d-%H-%M-%S',
                        '%Y-%m-%d--%H-%M-%S',
                        '%y_%m_%dT%H_%M_%S',
                        '%Y-%m-%d%H-%M-%S',
                        '%Y%m%d-%H%M%S',
                        '%Y%m%d-%H%M',
                        '%Y-%m-%d',
                        '%Y%m%d',
                        '%m_%d_%Y',
                        '%m_%d_%y',
                        '%m%d%y',
                        '%m%d%Y']

        mapping = [('%Y', '(20\d{2})'), ('%y', '(\d{2})'), ('%d', '(\d{2})'), ('%m', '(\d{2})'),
                   ('%H', '(\d{2})'), ('%M', '(\d{2})'), ('%S', '(\d{2})')]

        time_regexes = []
        for time_format in time_formats:
            for k, v in mapping:
                time_format = time_format.replace(k, v)
            time_regexes.append(time_format)

        for time_regex, time_format in zip(time_regexes, time_formats):
            try:
                mat = re.findall('(?<!\d)(%s)(?!\d)' % time_regex, name)
                if mat is not None:
                    return datetime.datetime.strptime(mat[0][0], time_format)
            except (ValueError, IndexError) as e:
                pass
        return None

    @staticmethod
    def _get_abbrs(input_string, output_length=0):
        """ Generates abbreviations for input_string
        Args:
            input_string (str): name of object
            output_length (num): optional specific length of abbreviations, default is off
        Returns: [str]: list of all combinations that include the first letter (possible abbreviations)
        """
        for i, j in itertools.combinations(range(len(input_string[1:]) + 1), 2):
            abbr = input_string[0] + input_string[1:][i:j]
            if output_length and len(abbr) == output_length:
                yield abbr
            elif output_length == 0:
                yield abbr

    @staticmethod
    def _get_casing_permutations(input_string):
        """ Takes a string and gives all possible permutations of casing for comparative purposes
        Args:
            input_string (str): name of object
        Yields: (str): iterator of all possible permutations of casing for the input_string
        """
        if not input_string:
            yield ""
        else:
            first = input_string[:1]
            if first.lower() == first.upper():
                for sub_casing in NameParser._get_casing_permutations(input_string[1:]):
                    yield first + sub_casing
            else:
                for sub_casing in NameParser._get_casing_permutations(input_string[1:]):
                    yield first.lower() + sub_casing
                    yield first.upper() + sub_casing

    @staticmethod
    def _valid_camel(input_string):
        """ Checks to see if an input string is valid for use in camel casing
        Args:
            input_string (str): input word
        Returns (bool): whether it is valid or not
        """
        regex = r'[A-Z]+[a-z]*'
        matches = re.findall(regex, input_string)
        if len(matches) == 1 and matches[0] == input_string:
            return True
        return False