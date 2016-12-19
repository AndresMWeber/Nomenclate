#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
from imp import reload
import re
import string
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions


class NameAttr(object):
    def __init__(self, value=None, label=None):
        self.value = value if value is not None else ""
        self.label = label

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class Nomenclate(object):
    """This class deals with renaming of objects in an approved pattern
    """
    CONFIG_PATH = ['overall_config']

    SUFFIXES_FORMAT_PATH = ['suffixes']
    NAMING_FORMAT_PATH = ['naming_formats']
    DEFAULT_FORMAT_PATH = NAMING_FORMAT_PATH + ['node', 'default']

    OPTIONS_PATH = ['options']
    VARIATION_PATH = OPTIONS_PATH + ['var']
    SIDE_PATH = OPTIONS_PATH + ['side']

    FORMAT_STRING_REGEX = r'([A-Za-z][^A-Z_.]*)'

    def __init__(self, **kwargs):
        self.cfg = config.ConfigParse()

        self.index = 0
        self.format_order = None
        self.format_string = None

        self.suffix_table = None

        self.reset_from_config()
        self.merge_dict(kwargs)

    @property
    def tokens(self):
        return list(self.state)

    @property
    def state(self):
        return dict((name_attr.label, name_attr.value) for name_attr in self.get_token_attrs())

    @state.setter
    def state(self, input_object, **kwargs):
        """
        Args:
            input_object Union[dict, self.__class__]: accepts a dictionary or self.__class__
        """
        if isinstance(input_object, self.__class__):
            input_object = input_object.state

        for input_attr_name, input_attr_value in iteritems(input_object):
            if input_attr_name in self.format_order:
                self.__dict__.get(input_attr_name).set(input_attr_value)
            else:
                setattr(self, input_attr_name, NameAttr(value=input_attr_value, label=input_attr_name))

        self.merge_dict(kwargs)

    def reset_from_config(self):
        self.initialize_config_settings()
        self.initialize_format_options(self.DEFAULT_FORMAT_PATH)
        self.initialize_options()
        self.initialize_ui_options()

    def initialize_config_settings(self):
        for setting, value in iteritems(self.cfg.get(self.CONFIG_PATH, return_type=dict)):
            setattr(self, setting, value)

    def initialize_format_options(self, format_target):
        """
        Args:
            format_target Union[str, list]: can be either a query path to a format
                                            or in format of a naming string the sections should be spaced around
                                              e.g. - this_is_a_naming_string
        Returns None: raises IOError if failure
        """
        try:
            self._validate_format_string(format_target)
            self.format_string = format_target
        except exceptions.FormatError:
            try:
                format_target = format_target if isinstance(format_target, list) else [format_target]
                self.format_string = self.cfg.get(format_target, return_type=str)
            except exceptions.ResourceNotFoundError:
                # TODO: Should log a default setting due to no target found.
                self.format_string = self.cfg.get(self.DEFAULT_FORMAT_PATH, return_type=str)
        finally:
            self.format_order = self.get_format_order_from_format_string(self.format_string)
            self.build_name_attrs()

    def initialize_options(self):
        self.naming_formats = self.cfg.get(self.NAMING_FORMAT_PATH, return_type=dict)
        self.config_table = self.cfg.get(self.CONFIG_PATH, return_type=dict)
        self.suffix_table = self.cfg.get(self.SUFFIXES_FORMAT_PATH, return_type=dict)

    def initialize_ui_options(self):
        """
        Placeholder for all categories/sub-lists within options to be recorded here
        """
        pass

    def build_name_attrs(self):
        """ Creates all necessary name attributes for the naming convention
        """
        self.purge_invalid_name_attrs()
        for token in self.format_order:
            try:
                self._get_token_attr(token)
            except exceptions.SourceError:
                self._set_token_attr(token, "")

    def purge_invalid_name_attrs(self):
        """ Removes name attrs not found in the format order
        """
        for token_attr in self.get_token_attrs():
            try:
                self._validate_name_in_format_order(token_attr.label)
            except exceptions.FormatError:
                delattr(self, token_attr)

    def purge_name_attrs(self):
        for token_attr in self.get_token_attrs():
            delattr(self, token_attr)

    def clear_name_attrs(self):
        for token_attr in self.get_token_attrs():
            token_attr.set('')

    def merge_dict(self, input_dict):
        """ updates the current set of NameAttrs with new or overwritten values from a dictionary
        Args:
            kwargs (dict): any extra definitions you want to input into the resulting dictionary
        Returns (dict): dictionary of relevant values
        """
        for key, value in iteritems(input_dict):
            self._set_token_attr(key, value)

    def get_format_order_from_format_string(self, format_string):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
                http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters
        Returns [string]: list of the matching tokens
        """
        try:
            #TODO: probably needs lots of error checking, need to write a test suite.
            pattern = re.compile(self.FORMAT_STRING_REGEX)
            return pattern.findall(format_string)
        except TypeError:
            raise exceptions.FormatError('Format string %s is not a valid input type, must be <type str>' %
                                         format_string)

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        # TODO: This should be a complete rewrite.  It's insanity.
        # Need to use deep copy to do a true snapshot of current settings without manipulating them
        dict_buffer = self.get_dict()

        # Set whatever the user has specified if it's a valid format token
        for key, value in iteritems(kwargs):
            if self.check_valid_format(key):
                dict_buffer[key] = value

        result = self.format_string

        for key, attr in iteritems(dict_buffer):
            if key in result:
                token_raw = attr
                if token_raw:
                    replacement = str(token_raw)
                    # Check if the token is an actual suffix (from the UI)
                    if token_raw in [v for k, v in iteritems(self.suffix_table)]:
                        replacement = token_raw

                    # Or check through the suffix dictionary for a match
                    elif key == 'type':
                        replacement = self.suffix_table.get(token_raw, "")

                    if key in self.format_capitals and self.camel_case:
                        replacement = replacement.title()

                    # Now replace the token with the input
                    result = result.replace('{' + key + '}', replacement)

        return self.cleanup_formatted_string(result)

    def get_token_attrs(self):
        return [token for token in self.__dict__ if isinstance(token, NameAttr)]

    def get_chain(self, end, start=None, **kwargs):
        """ Returns a list of names based on index values
        Args:
            end (int): integer for end of sequence
            start (int): optional definition of start position
        Returns (list): generated object names
        """
        # TODO: rework this entire function, very dirty function.
        var_attr = self._get_token_attr(self.VARIATION_PATH[-1])
        var_orig = var_attr.get()

        var_start, n_type = self._get_alphanumeric_index(var_orig)

        if start is None:
            start = var_start
        names = []
        for index in range(start, end + 1):
            if n_type in ['char_hi', 'char_lo']:
                capital = True if n_type == 'char_hi' else False
                var_attr.set(self.get_variation_id(index, capital))

            else:
                var_attr.set(str(index))
            if 'var' in kwargs:
                kwargs.pop("var", None)
            names.append(self.get(**kwargs))
        var_attr.set(var_orig)
        return names

    def _set_token_attr(self, token, value):
        token_attrs = self.get_token_attrs()

        if token not in [token_attr.parent for token_attr in token_attrs]:
            setattr(self, token, NameAttr(value=value, label=token))
        else:
            for token_attr in token_attrs:
                if token == token_attr.parent:
                    token_attr.set(value)

    def _get_token_attr(self, token):
        token_attr = self.__dict__.get(token)
        if token_attr is None:
            raise exceptions.SourceError('This nomenclate instance has no %s attribute set.' % token)
        else:
            return token_attr

    def _validate_format_string(self, format_target):
        """ Checks to see if the target format string follows the proper style
        """
        format_order = self.get_format_order_from_format_string(format_target)
        if format_target != '_'.join(format_order):
            raise exceptions.FormatError("You have specified an invalid format string %s." % format_target)

    def _validate_name_in_format_order(self, name):
        """ For quick checking if a key token is part of the format order
        """
        if name not in self.format_order:
            raise exceptions.FormatError('The name token %s is not found in the current format string' %
                                         self.format_string)

    @staticmethod
    def _get_alphanumeric_index(query_string):
        """ Given an input string of either int or char, returns what index in the alphabet and case it is
        Args:
            query_string (str): query string
        Returns [int, str]: list of the index and type
        """
        #TODO: could probably rework this. it works, but it's ugly as hell.
        try:
            return [int(query_string), 'int']
        except ValueError:
            if len(query_string) == 1:
                if query_string.isupper():
                    return [string.uppercase.index(query_string), 'char_hi']
                elif query_string.islower():
                    return [string.lowercase.index(query_string), 'char_lo']
            else:
                raise IOError('The input is a string longer than one character')
        return [0, 'char_hi']

    @staticmethod
    def cleanup_formatted_string(formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores
        Args:
            formatted_string (string): string that has had tokens replaced
        Returns (string): cleaned up name of object
        """
        # TODO: chunk this out to sub-processes for easier error checking, could be own class
        # Remove whitespace
        result = formatted_string.replace(' ', '')
        # Remove any tokens that still exist that were unformatted
        pattern = r'(\{\w*\})'
        result = re.sub(pattern, '', result)
        # Remove any multiple underscores
        result = re.sub('_+', '_', result)
        # Remove trailing or preceding underscores
        result = re.match(r'^_*(.*?)_*$', result)
        if result:
            return result.groups()[0]
        else:
            return result

    @staticmethod
    def get_variation_id(integer, capital=False):
        """ Convert an integer value to a character. a-z then double aa-zz etc
        Args:
            integer (int): integer index we're looking up
            capital (bool): whether we convert to capitals or not
        Returns (str): alphanumeric representation of the index
        """
        # calculate number of characters required
        base_power = base_start = base_end = 0
        while integer >= base_end:
            base_power += 1
            base_start = base_end
            base_end += pow(26, base_power)
        base_index = integer - base_start

        # create alpha representation
        alphas = ['a'] * base_power
        for index in range(base_power - 1, -1, -1):
            alphas[index] = chr(97 + (base_index % 26))
            base_index /= 26

        characters = ''.join(alphas)
        return characters.upper() if capital else characters

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            equal = False
            self_attrs = self.get_token_attrs()
            other_attrs = other.get_token_attrs()
            if len(self_attrs) > len(other_attrs):
                return False

            for attr in self_attrs:
                for other_attr in other_attrs:
                    if attr.val == other_attr.val:
                        equal = True
                        break
                    else:
                        equal = False
            return equal
        return False

    def __repr__(self):
        return self.get()
