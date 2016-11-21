#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
from imp import reload
from six import string_types
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
        print('input is ', name)
        sides = config.ConfigParse().get_subsection(section='options', subsection='side')
        for side in sides:
            # Have to check for longest first and remove duplicates
            abbreviations = list(set(cls._get_abbrs(side)))
            abbreviations.sort(key=len, reverse=True)

            for abbr in abbreviations:
                # We won't check for abbreviations that are stupid eg something with apparent camel casing within
                # the word itself like LeF, sorting from:
                # http://stackoverflow.com/questions/13954841/python-sort-upper-case-and-lower-case
                casing_permutations = list(set(cls._get_casing_permutations(abbr)))
                casing_permutations.sort(key=lambda v: (v.upper(), v[0].islower(), len(v)))
                for permutation in casing_permutations:
                    if not cls._valid_camel(permutation):
                        continue
                    separators = r'[ ,_\-!?:]'

                    abbr_island = r'[{SEP}]+({ABBR})[{SEP}]+'
                    abbr_seos = r'(?:^|[a-z]|{SEP})({ABBR})(?:$|[A-Z][a-z]+|{SEP})'
                    abbr_camel = r'(?:[a-z])({ABBR})(?:$|[A-Z]|{SEP})'

                    patterns = [abbr_seos,
                                abbr_island,
                                abbr_camel]

                    # One check for camel casing exception case
                    if not permutation[0].isupper():
                        patterns.remove(abbr_camel)

                    print('\t', permutation)
                    for pattern in patterns:
                        match = cls._get_regex_search(name, pattern.format(ABBR=permutation, SEP=separators))
                        if match:
                            match.update({'side': side})
                            return match

        return None

    @classmethod
    def get_base(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix)
        Args:
            name (str): string that represents a possible name of an object
        Returns (str): the detected basename
        """
        parse_sections = ['basename', 'version', 'date', 'side', 'udim']
        parse_dict = dict.fromkeys(parse_sections, None)

        parse_dict['date'] = cls.get_date(name) if cls.get_date(name) else None
        parse_dict['version'] = cls.get_version(name)
        parse_dict['udim'] = str(cls.get_udim(name)) if cls.get_udim(name) else None
        parse_dict['side'] = cls.get_side(name)
        print('name ', name, 'parse_dict ', parse_dict)

        for parse_section in parse_sections:
            try:
                print(parse_dict[parse_section])
                word = parse_dict[parse_section]
                # TODO: REPLACE VIA POSITION
                if isinstance(word, string_types):
                    word = [word]

                print('before replacement ', name)
                for replacement in word:
                    print('trying to replace ', replacement)
                    name = name.replace(replacement, '')

                print('after replacement ', name)
            except (IndexError, TypeError) as e:
                pass

        regex_basename = '(?:^[-._]+)?([a-zA-Z0-9_\-|]+?)(?=[-._]{2,}|\.)'
        try:
            parse_dict['basename'] = re.findall(regex_basename, name)[0]
        except IndexError:
            parse_dict['basename'] = None
        print(parse_dict)
        return parse_dict

    @classmethod
    def get_discipline(cls, name):
        raise NotImplementedError

    @classmethod
    def get_version(cls, name):
        """ Checks a string for a possible version of an object (no prefix, no suffix).
            Assumes only up to 4 digit padding
        Args:
            name (str): string that represents a possible name of an object
        Returns (float|int, [str]): gets the version number as a float or int if whole then the string matches or None
        """
        # Dates can confuse this stuff, so we'll check for that first and remove it from the string if found
        date = cls.get_date(name)
        if date:
            formatted_date = date['datetime'].strftime(date['format'])
            name = name.replace(formatted_date, '')

        regex = '(?:^|[a-z]{2,}|[._-])([vV]?[0-9]{1,4})(?=[._-]|$)'
        matches = re.findall(regex, name)
        if matches:
            match_numbers = [int(match.upper().replace('V', '')) for match in matches]
            if len(matches) > 1:
                # Two or more version numbers so we can assume this is trying to get sub versions for the
                # last two found, so return as decimal value
                return match_numbers[-2] + match_numbers[-1]*.1, matches[-2:]
            return match_numbers[-1], matches[-1:]
        return None

    @classmethod
    def get_udim(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix)
        Args:
            name (str): string that represents a possible name of an object
        Returns (int): the last found match because convention keeps UDIM markers at the end.
        """
        print (name)
        match = cls._get_regex_search(name, '(?:[a-zA-Z]|[._-])(1[0-9]{3})(?:[._-])', first_match=False)
        if match:
            print(match)
            match.update({'match_int': int(match['match'])})
            return match
        print(' NO MATCH')
        return None

    @classmethod
    def get_date(cls, name):
        """ Checks a string for a possible date formatted into the name.  It assumes dates do not have other
            numbers at the front or head of the date.  Currently only supports dates in 1900 and 2000.
            Heavily relies on datetime for error checking to see
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
                        '%m%d%Y',
                        '%d_%m_%Y',
                        '%Y']

        mapping = [('%Y', '((19|20)\d{2})'), ('%y', '(\d{2})'), ('%d', '(\d{2})'), ('%m', '(\d{2})'),
                   ('%H', '(\d{2})'), ('%M', '(\d{2})'), ('%S', '(\d{2})')]
        time_regexes = []
        for time_format in time_formats:
            for k, v in mapping:
                time_format = time_format.replace(k, v)
            time_regexes.append(time_format)

        for time_regex, time_format in zip(time_regexes, time_formats):
            match = cls._get_regex_search(name, '(?<!\d)(%s)(?!\d)' % time_regex)
            if match:
                try:
                    match.update({'format': time_format,
                                  'datetime': datetime.datetime.strptime(match['match'], time_format)})
                    return match
                except ValueError:
                    pass
        return None

    @staticmethod
    def _get_regex_search(input_string, regex, first_match=True):
        """ Using this so that all results from the functions return similar results
        Args:
            input_string (str): input string to be checked
            regex (str): input regex to be compiled and searched with
            first_match (bool): whether to get first or last match, if false, last match provided
        Returns (dict): dictionary of matches or empty dict
        """
        generator = re.compile(regex).finditer(input_string)
        match = {}
        for obj in generator:
            match = {'pattern': regex,
                     'input': input_string,
                     'position': obj.span(1),
                     'position_full': obj.span(),
                     'match': obj.group(1),
                     'match_full': obj.group()}
            if first_match:
                return match
                break
        return match


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
            if len(abbr) == output_length:
                yield abbr
            elif output_length == 0:
                yield abbr
        # Have to add the solitary letter as well
        if not output_length or output_length == 1:
            yield input_string[0]

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
        elif len(input_string) == 1:
            return True
        return False
