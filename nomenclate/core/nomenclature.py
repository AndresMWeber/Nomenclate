#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
from imp import reload
import re
import string
import nomenclate.core.configurator as config


class NameAttr(object):
    def __init__(self, value = None, parent = None):
        self.value = value if value is not None else ""
        self.namer = parent

    def set(self, value):
        self.value = value
    
    def get(self):
        return self.value


class Nomenclate(object):
    """This class deals with renaming of objects in an approved pattern
    """
    NAMING_FORMAT_HEADER_PATH = ['naming_formats']
    DEFAULT_FORMAT_PATH = NAMING_FORMAT_HEADER_PATH + ['node', 'default']
    def __init__(self, **kwargs):
        """ Set default a
        """
        self.cfg = config.ConfigParse()

        self.format_order = None
        self.format_string = None

        self.suffix_LUT = None

        self.refresh()
        self.init_from_suffix_lut()
        self.reset(kwargs)

    #TODO: add verbosity to function name
    def refresh(self):
        """ Refresh the data from the look up table
        """
        # Setting initial options from config file
        for setting, value in iteritems(self.cfg.get('overall_config', return_type=dict)):
            setattr(self, setting, value)

        self.initialize_format_options(self.DEFAULT_FORMAT_PATH)
        self.initialize_options_from_config_file()
        self.initialize_ui_options()

    def initialize_format_options(self, format_target):
        """
        Args:
            format_target (str): can be either a subsection in the formats area or in format of a naming string
                                 e.g. - this_is_a_naming_string
                                 the sections should be spaced around
        Returns None: raises IOError if failure
        """
        try:
            format_target = format_target if isinstance(format_target, list) else [format_target]
            try:
                self._validate_format_string(format_target)
                self.format_string = format_target
            except:
                self.format_string = self.cfg.get(self.DEFAULT_FORMAT_PATH, return_type=str)
            self.format_order = self.get_format_order(self.format_string)
            self.build_name_attrs()
        #TODO: Custom error!!!!
        except IOError:
            raise IOError('Could not find naming format %s in config file nor was it a valid naming format' % format_target)

    def initialize_options_from_config_file(self):
        self.naming_formats = self.cfg.get('naming_formats', return_type=dict)
        self.config_LUT = self.cfg.get('overall_config', return_type=dict)
        self.suffix_LUT =  self.cfg.get('suffixes', return_type=dict)


    def initialize_ui_options(self):
        """
        Placeholder for all categories/sub-lists within options to be recorded here
        """
        pass

    @staticmethod
    def get_format_order(format_string):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
                http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters
        Returns [string]: list of the matching tokens
        """
        pattern = re.compile(r'([A-Za-z][^A-Z_.]*)')
        return pattern.findall(format_string)

    def build_name_attrs(self):
        """ Creates all necessary name attributes for the naming convention
        """
        self.purge_name_attrs()
        for token in self.format_order:
            if token not in self.__dict__:
                setattr(self, token, NameAttr(parent=self))

    def purge_name_attrs(self):
        """ Removes name attrs not found in the format order
        """
        for token_attr in self.get_token_attrs():
            if token_attr not in self.format_order:
                delattr(self, token_attr)

    def init_from_suffix_lut(self):
        """ Initialize all the needed attributes for the format order to succeed
        """
        for format_key in self.format_order:
            if format_key not in self.__dict__:
                setattr(self, format_key, NameAttr("", self))

    def reset(self, input_settings_data={}):
        """ Re-Initialize all the needed attributes for the format order to succeed
        Args:
            input_settings_data (dict): any overrides the user wants to specify instead of reset to ""
        Returns None
        """
        #TODO: change settings in a similar way as configurator with a registry handler setup.
        if isinstance(input_settings_data, str) or isinstance(input_settings_data, unicode):
            input_settings_data = {'name': input_settings_data}

        # Now replace all self.__dict__ attributes to a NameAttr with the given values
        for format_key in self.format_order:
            setattr(self, format_key, NameAttr(input_settings_data.get(format_key), self))

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        # TODO: This should be a complete rewrite.  It's insanity.
        # Need to use deep copy to do a true snapshot of current settings without manipulating them
        dict_buffer = self.get_dict()

        # Set whatever the user has specified if it's a valid format token
        for key, value in iteritems(kwargs):
            if self._is_format(key):
                dict_buffer[key] = value

        result = self.format_string

        for key, attr in iteritems(dict_buffer):
            if key in result:
                token_raw = attr
                if token_raw:
                    replacement = str(token_raw)
                    # Check if the token is an actual suffix (from the UI)
                    if token_raw in [v for k, v in iteritems(self.suffix_LUT)]:
                        replacement = token_raw

                    # Or check through the suffix dictionary for a match
                    elif key == 'type':
                        replacement = self.suffix_LUT.get(token_raw, "")

                    if key in self.format_capitals and self.camel_case:
                        replacement = replacement.title()

                    # Now replace the token with the input
                    result = result.replace('{'+key+'}', replacement)

        return self.cleanup_formatted_string(result)

    def get_dict(self, **kwargs):
        """ Returns a dictionary of relevant attribute values to set a new nomenclate or build a new one
        Args:
            kwargs (dict): any extra definitions you want to input into the resulting dictionary
        Returns (dict): dictionary of relevant values
        """
        # Get every possible NameAttr out of the Nomenclate object
        format_tokens = []
        output={}
        for key, value in iteritems(self.__dict__):
            if self._is_format(key):
                 output[key] = self.__dict__.get(key).get()

        # Now add in any extras the user wanted to override
        for key, value in iteritems(kwargs):
            if self._is_format(key) and isinstance(value, str):
                output[key] = value

        return output

    def get_chain(self, end, start=None, **kwargs):
        """ Returns a list of names based on index values
        Args:
            end (int): integer for end of sequence
            start (int): optional definition of start position
        Returns (list): generated object names
        """
        var_orig = self.var.get()

        var_start, n_type = self._get_alphanumeric_index(self.var.get())
        # Just in case the start hasn't been overridden it's based on the current var_opt index
        if start is None:
            start = var_start
        names = []
        for index in range(start, end+1):
            if n_type in ['char_hi', 'char_lo']:
                capital = True if n_type == 'char_hi' else False
                self.var.set(self.get_variation_id(index, capital))

            else:
                self.var.set(str(index))
            if 'var' in kwargs:
                kwargs.pop("var", None)
            names.append(self.get(**kwargs))
        self.var.set(var_orig)
        return names


    def get_token_attrs(self):
        return [token for token in self.__dict__ if isinstance(token, NameAttr)]

    def get_state(self, input_dict=None):
        """ Returns the current state of dictionary items with hashes to resolve conflicts
        """
        if input_dict is None:
            input_dict = self.__dict__
        if input_dict:
            input_dict = self.get_token_attrs()
            return {item: (input_dict[item].get(), item.__hash__()) for (item, value) in input_dict}
        return None

    @staticmethod
    def _get_alphanumeric_index(query_string):
        """ Given an input string of either int or char, returns what index in the alphabet and case it is
        Args:
            query_string (str): query string
        Returns [int, str]: list of the index and type
        """
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

    def _is_format(self, name):
        """ For quick checking if a key is part of the format order
        Args:
            name (str): a name of a possible attribute for in a nomenclate string
        """
        if name in self.format_order:
            return True
        return False


    @staticmethod
    def cleanup_formatted_string(formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores
        Args:
            formatted_string (string): string that has had tokens replaced
        Returns (string): cleaned up name of object
        """
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

    def _validate_format_string(self, format_target):
        #TODO: raise validationerror!!!!!!!!! fuck this true false shit
        format_order = self.get_format_order(format_target)
        if format_target != '_'.join(format_order):
            raise ValueError ("This should be a custom error, but the format %s is not valid." % format_target)

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
