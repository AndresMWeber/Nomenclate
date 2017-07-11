#!/usr/bin/env python
""" This module does name parsing to recover information about the name based on common conventions.
    it will be very prone to missing information since names will be very variable, but hopefully
    it will be more intelligent as time goes on
"""
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from six import iteritems
import re
import datetime
import itertools
from . import configurator as config


class NameParser(object):
    """ This parses names of assets.  It assumes the usual convention of strings separated by underscores.

    """
    CONFIG_SIDES = config.ConfigParse().get(['options', 'side'])
    CONFIG_DISCIPLINES = config.ConfigParse().get(['options', 'discipline'])
    PARSABLE = ['basename', 'version', 'date', 'side', 'udim']

    REGEX_BASENAME = r'(?:^[-._]+)?([a-zA-Z0-9_\-|]+?)(?=[-._]{2,}|\.)'
    REGEX_SEPARATORS = r'[ ,_!?:\.\-]'

    REGEX_ABBR_ISLAND = r'(?:[{SEP}]+)({ABBR})(?:[{SEP}]+)'
    REGEX_ABBR_SEOS = r'(?:^|[a-z]|{SEP})({ABBR})(?:$|[A-Z][a-z]+|{SEP})'
    REGEX_ABBR_CAMEL = r'(?:[a-z])({ABBR})(?:$|[A-Z]|{SEP})'

    REGEX_VERSION = r'(?:^|[a-z]{{2,}}[a-uw-z]+|{SEP}[a-z]?[a-uw-z]+|{SEP})([vV]?[0-9]{{1,4}})(?={SEP}|$)'
    REGEX_UDIM = r'(?:[a-zA-Z]|[._-])(1[0-9]{3})(?:[._-])'
    REGEX_DATE = r'(?<!\d)(%s)(?!\d)'
    REGEX_CAMEL = r'(?:{SEP}?)((?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z]))(?:{SEP}?)'

    @classmethod
    def parse_name(cls, name):
        """ Parses a name into a dictionary of identified subsections with accompanying information to
            correctly identify and replace if necessary

        :param name: str, string to be parsed
        :return: dict, dictionary with relevant parsed information
        """
        parse_dict = dict.fromkeys(cls.PARSABLE, None)
        parse_dict['date'] = cls.get_date(name)
        parse_dict['version'] = cls.get_version(name)
        parse_dict['udim'] = cls.get_udim(name)
        parse_dict['side'] = cls.get_side(name)
        parse_dict['basename'] = cls.get_base_naive(cls._reduce_name(name, parse_dict))
        return parse_dict

    @classmethod
    def get_side(cls, name, ignore=''):
        """ Checks a string for a possible side string token, this assumes its on its own
            and is not part of or camel cased and combined with a word.  Returns first found side to reduce duplicates.
            We can be safe to assume the abbreviation for the side does not have camel casing within its own word.

        :param name: str, string that represents a possible name of an object
        :param name: str, string that represents a possible name of an object
        :return: (None, str), either the found permutation of the side found in name or None
        """
        for side in cls.CONFIG_SIDES:
            """ Tried using a regex, however it would've taken too long to debug
            side_regex = cls._build_abbreviation_regex(side)
            result = cls._generic_search(name, side_regex, metadata={'side': side}, ignore=ignore)
            if result:
                return result
            """
            for permutations in cls.get_string_camel_patterns(side):
                for permutation in permutations:
                    result = cls._generic_search(name, permutation, metadata={'side': side}, ignore=ignore)
                    if result:
                        return result
        return None

    @classmethod
    def get_discipline(cls, name, ignore='', min_length=3):
        """ Checks a string for a possible discipline string token, this assumes its on its own
            and is not part of or camel cased and combined with a word.  Returns first found match to reduce duplicates.
            We can be safe to assume the abbreviation for the discipline does not have camel casing within its own word.

        :param name: str, the string based object name
        :param ignore: str, specific ignore string for the search to avoid
        :param min_length: int, minimum length for possible abbreviations of disciplines. Lower = more wrong guesses.
        :return: dict, match dictionary
        """
        for discipline in cls.CONFIG_DISCIPLINES:
            re_abbr = '({RECURSE}(?=[0-9]|[A-Z]|{SEPARATORS}))'.format(
                RECURSE=cls._build_abbreviation_regex(discipline),
                SEPARATORS=cls.REGEX_SEPARATORS)
            matches = cls._get_regex_search(name, re_abbr, ignore=ignore)
            if matches:
                matches = [m for m in matches if
                           re.findall('([a-z]{%d,})' % min_length, m['match'], flags=re.IGNORECASE)]
                if matches:
                    return matches[-1]
        return None

    @classmethod
    def get_base(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix).
            We need to do a full parse to make sure we've ruled out all the possible other parse queries

        :param name: str, string that represents a possible name of an object
        :return: str, the detected basename
        """
        return cls.parse_name(name).get('basename', None)

    @classmethod
    def get_base_naive(cls, name, ignore=''):
        """ Checks a string for a possible base name of an object (no prefix, no suffix).
            We need to do a full parse to make sure we've ruled out all the possible other parse queries

        :param name: str, string that represents a possible name of an object
        :return: str, the detected basename
        """
        return cls._get_regex_search(name, cls.REGEX_BASENAME, match_index=0, ignore=ignore)

    @classmethod
    def get_version(cls, name):
        """ Checks a string for a possible version of an object (no prefix, no suffix).
            Assumes only up to 4 digit padding

        :param name: str, string that represents a possible name of an object
        :return: (float, int, list(str), None), gets the version number then the string matches
        """
        # Dates can confuse th
        # is stuff, so we'll check for that first and remove it from the string if found
        try:
            date = cls.get_date(name)
            date = date['datetime'].strftime(date['format'])
        except TypeError:
            pass
        return cls.get_version_naive(name, ignore=date or '')

    @classmethod
    def get_version_naive(cls, name, ignore=''):
        """ Checks a string for a possible version of an object (no prefix, no suffix) without filtering date out
            Assumes only up to 4 digit padding

        :param name: str, string that represents a possible name of an object
        :return: (float, int, list(str), None), gets the version number then the string matches
        """
        match = cls._get_regex_search(name, cls.REGEX_VERSION.format(SEP=cls.REGEX_SEPARATORS), ignore=ignore)

        if match is not None:
            if len(match) > 1:
                for m in match:
                    m.update({'version': int(m['match'].upper().replace('V', ''))})
                compound_version = '.'.join([str(m['version']) for m in match])
                compound_version = float(compound_version) if compound_version.count('.') == 1 else compound_version
                return {'compound_matches': match,
                        'compound_version': compound_version,
                        'pattern': match[0]['pattern'],
                        'input': match[0]['input']}

            elif len(match) == 1:
                match = match[0]
                match.update({'version': int(match['match'].upper().replace('V', ''))})
                return match

        return None

    @classmethod
    def get_udim(cls, name):
        """ Checks a string for a possible base name of an object (no prefix, no suffix)

        :param name: str, string that represents a possible name of an object
        :returns: int, the last found match because convention keeps UDIM markers at the end.
        """
        match = cls._get_regex_search(name, cls.REGEX_UDIM, match_index=-1)
        if match:
            match.update({'match_int': int(match['match'])})
            return match
        return None

    @classmethod
    def get_short(cls, name):
        """ Returns the short name of a Maya asset name or path

        :param name: str, string that represents a possible name of an object
        :return: str, the short name of the maya node
        """
        return name.split('|')[-1].split('//')[-1]

    @classmethod
    def get_date(cls, name):
        """ Checks a string for a possible date formatted into the name.  It assumes dates do not have other
            numbers at the front or head of the date.  Currently only supports dates in 1900 and 2000.
            Heavily relies on datetime for error checking to see
            if date is actually viable. It follows similar ideas to this post:
            http://stackoverflow.com/questions/9978534/match-dates-using-python-regular-expressions

        :param name: str, string that represents a possible name of an object
        :return: datetime.datetime, datetime object with current time or None if not found
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
                        '%Y',
                        '%m-%d-%yy',
                        '%m%d%Y']

        mapping = [('%yy', '(([01]\d{1}))'), ('%Y', '((19|20)\d{2})'), ('%y', '(\d{2})'), ('%d', '(\d{2})'),
                   ('%m', '(\d{2})'),
                   ('%H', '(\d{2})'), ('%M', '(\d{2})'), ('%S', '(\d{2})')]
        time_regexes = []
        for time_format in time_formats:
            for k, v in mapping:
                time_format = time_format.replace(k, v)
            time_regexes.append(time_format)

        for time_regex, time_format in zip(time_regexes, time_formats):
            match = cls._get_regex_search(name,
                                          cls.REGEX_DATE % time_regex,
                                          metadata={'format': time_format},
                                          match_index=0)
            if match:
                try:
                    match.update({
                        'datetime': datetime.datetime.strptime(match['match'], time_format.replace('%yy', '%y'))
                    })
                    return match
                except ValueError:
                    pass
        return None

    @classmethod
    def get_string_camel_patterns(cls, name, min_length=0):
        """ Finds all permutations of possible camel casing of the given name

        :param name: str, the name we need to get all possible permutations and abbreviations for
        :param min_length: int, minimum length we want for abbreviations
        :return: list(list(str)), list casing permutations of list of abbreviations
        """
        # Have to check for longest first and remove duplicates
        patterns = []
        abbreviations = list(set(cls._get_abbreviations(name, output_length=min_length)))
        abbreviations.sort(key=len, reverse=True)

        for abbr in abbreviations:
            # We won't check for abbreviations that are stupid eg something with apparent camel casing within
            # the word itself like LeF, sorting from:
            # http://stackoverflow.com/questions/13954841/python-sort-upper-case-and-lower-case
            casing_permutations = list(set(cls._get_casing_permutations(abbr)))
            casing_permutations.sort(key=lambda v: (v.upper(), v[0].islower(), len(v)))
            permutations = [permutation for permutation in casing_permutations if
                            cls.is_valid_camel(permutation) or len(permutation) <= 2]
            if permutations:
                patterns.append(permutations)

        return patterns

    @classmethod
    def _reduce_name(cls, name, parse_dict):
        """ Reduces a name against matches found in a parse dictionary

        :param name: str, name to be reduced
        :param parse_dict: dict, dictionary of matches to reduce against
        :return: str, reduced string
        """
        # Now remove all found entries to make basename regex have an easier time
        removal_indices = []
        for section, match in iteritems(parse_dict):
            try:
                matches = []
                if isinstance(match, dict) and 'compound_matches' in match:
                    matches = match.get('compound_matches')
                elif not isinstance(match, list) and match is not None:
                    matches = [match]

                for m in matches:
                    valid_slice = True
                    slice_a, slice_b = m.get('position')
                    # Adjust slice positions from previous slices
                    if removal_indices is []:
                        removal_indices.append((slice_a, slice_b))

                    for r_slice_a, r_slice_b in removal_indices:
                        if slice_a == r_slice_a and slice_b == r_slice_b:
                            valid_slice = False
                        if slice_a > r_slice_a or slice_a > r_slice_b or slice_b > r_slice_b or slice_b > r_slice_a:
                            slice_delta = r_slice_b - r_slice_a
                            slice_a -= slice_delta
                            slice_b -= slice_delta

                    if valid_slice:
                        name = cls._string_remove_slice(name, slice_a, slice_b)
                        removal_indices.append((slice_a, slice_b))
            except (IndexError, TypeError):
                pass
        return name

    @staticmethod
    def _get_regex_search(input_string, regex, metadata={}, match_index=None, ignore='', flags=0):
        """ Using this so that all results from the functions return similar results

        :param input_string: str, input string to be checked
        :param regex: str, input regex to be compiled and searched with
        :param match_index: (int, None), whether to get a specific match, if None returns all matches as list
        :param metadata: dict, dictionary of extra meta tags needed to identify information
        :return: list(dict), list of dictionaries if multiple hits or a specific entry or None
        """
        generator = re.compile(regex, flags=flags).finditer(input_string)
        matches = []
        for obj in generator:
            try:
                span_a = obj.span(1)
                group_a = obj.group(1)
            except IndexError:
                span_a = obj.span()
                group_a = obj.group()

            if obj.groups() == ('',):
                # Not sure how to account for this situation yet, weird regex.
                return True

            if group_a not in ignore:
                matches.append({'pattern': regex,
                                'input': input_string,
                                'position': span_a,
                                'position_full': obj.span(),
                                'match': group_a,
                                'match_full': obj.group()})

        if matches:
            for match in matches:
                match.update(metadata)
            if match_index is not None:
                return matches[match_index]
            return matches
        return None

    @classmethod
    def _generic_search(cls, name, search_string, metadata={}, ignore=''):
        """ Searches for a specific string given three types of regex search types.  Also auto-checks for camel casing.

        :param name: str, name of object in question
        :param search_string: str, string to find and insert into the search regexes
        :param metadata: dict, metadata to add to the result if we find a match
        :param ignore: str, ignore specific string for the search
        :return: dict, dictionary of search results
        """
        patterns = [cls.REGEX_ABBR_SEOS,
                    cls.REGEX_ABBR_ISLAND,
                    cls.REGEX_ABBR_CAMEL]

        if not search_string[0].isupper():
            patterns.remove(cls.REGEX_ABBR_CAMEL)

        for pattern in patterns:
            search_result = cls._get_regex_search(name,
                                                  pattern.format(ABBR=search_string, SEP=cls.REGEX_SEPARATORS),
                                                  metadata=metadata,
                                                  match_index=0,
                                                  ignore=ignore)
            if search_result is not None:
                if cls.is_valid_camel(search_result.get('match_full'), strcmp=search_result.get('match')):
                    return search_result
        return None

    @staticmethod
    def _get_abbreviations(input_string, output_length=0):
        """ Generates abbreviations for input_string

        :param input_string: str, name of object
        :param output_length: int, optional specific length of abbreviations, default is off
        :return: list(str), list of all combinations that include the first letter (possible abbreviations)
        """
        for i, j in itertools.combinations(range(len(input_string[1:]) + 1), 2):
            abbr = input_string[0] + input_string[1:][i:j]
            if len(abbr) >= output_length:
                yield abbr
            elif output_length == 0:
                yield abbr
        # Have to add the solitary letter as well
        if not output_length or output_length == 1:
            yield input_string[0]

    @classmethod
    def is_valid_camel(cls, input_string, strcmp=None, ignore=''):
        """ Checks to see if an input string is valid for use in camel casing
            This assumes that all lowercase strings are not valid camel case situations and no camel string
            can just be a capitalized word.  Took ideas from here:
            http://stackoverflow.com/questions/29916065/how-to-do-camelcase-split-in-python

        :param input_string: str, input word
        :param strcmp: str, force detection on a substring just in case its undetectable
                            (e.g. part of a section of text that's all lowercase)
        :param ignore: str, what kind of string to ignore in the regex search
        :return: bool, whether it is valid or not
        """
        # clear any non chars from the string
        if not input_string:
            return False

        input_string = ''.join([c for c in input_string if c.isalpha()])
        matches = cls._get_regex_search(input_string,
                                        cls.REGEX_CAMEL.format(SEP=cls.REGEX_SEPARATORS),
                                        match_index=0,
                                        ignore=ignore)
        if matches or input_string == strcmp:
            if strcmp:
                index = input_string.find(strcmp) - 1
                is_camel = strcmp[0].isupper() and input_string[index].islower()
                is_input = strcmp == input_string
                is_start = index + 1 == 0
                return is_camel or is_input or is_start
            return True
        elif len(input_string) == 1:
            return True
        return False

    @staticmethod
    def _split_camel(name):
        """ Splits up a camel case name into its constituent components.

        :param name: str, name to split
        :return: list(str), list of components of the camel case string
        """
        return re.sub('(?!^)([A-Z][a-z]+)', r' \1', name).split()

    @classmethod
    def _get_casing_permutations(cls, input_string):
        """ Takes a string and gives all possible permutations of casing for comparative purposes

        :param input_string: str, name of object
        :return: Generator(str), iterator of all possible permutations of casing for the input_string
        """
        if not input_string:
            yield ""
        else:
            first = input_string[:1]
            for sub_casing in cls._get_casing_permutations(input_string[1:]):
                yield first.lower() + sub_casing
                yield first.upper() + sub_casing

    @staticmethod
    def _string_remove_slice(input_str, start, end):
        """ Removes portions of a string

        :param input_str: str, input string
        :param start: int, end search index
        :param end: int, start search index
        :return: str, the cut string
        """
        if 0 <= start < end <= len(input_str):
            return input_str[:start] + input_str[end:]
        return input_str

    @staticmethod
    def _build_abbreviation_regex(input_string):
        """ builds a recursive regex based on an input string to find possible abbreviations more simply.
            e.g. = punct(u(a(t(i(on?)?)?)?)?)?

        :param input_string: str, input string
        :return: str, output regex
        """
        result=''
        for char in input_string:
            result += '[%s%s]?' % (char.upper(), char.lower())
        return '(%s)' % result
