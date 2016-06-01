#!/usr/bin/env python
"""
.. module:: nomenclate
    :platform: None
    :synopsis: This module can name any asset according to a config file
    :plans: None
"""
__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"
__version__ = 1.1

# General imports
import re
import ConfigParser
import os
from collections import OrderedDict
import string
from copy import deepcopy

# Import my own setup to get the config file's path
from Forge.Forge import toolbox as tb
reload(tb)


class NameAttr(object):
    def __init__(self, val, parent):
        self.val = val
        self.namer = parent
        """ This proved too hard for me to handle...my imports fuck it.
        # Reading: http://stackoverflow.com/questions/13039060/proper-use-of-isinstanceobj-class
        if isinstance(parent, Nomenclate):
            self.val = val
            self.namer = parent
        else:
            print parent.__class__.__bases__
            print type(parent)
            raise TypeError("Parent of Attribute is not a Nomenclate type")
        """
    def set(self, v):
        self.val = v
    
    def get(self):
        return self.val
        
    def __deepcopy__(self, memo):
        return self


class Nomenclate(object):
    """This class deals with renaming of objects in an approved pattern
    """
    def __init__(self, **kwargs):
        """ Set default a
        """
        self.cfg = ConfigParse(tb.get_config_filepath())
        self.camel_case = True
        self.refresh()
        self.init_from_suffix_lut()
        self.set(kwargs)
    
    def set(self, name, **kwargs):
        """ Sets a nomenclate object from a dictionary
        Args:
            name (str or dict): string for the name or a dictionary that will update the current
        Returns (None):
        """
        if isinstance(name,str):
            self.name.set(name)
            
        elif isinstance(name, dict):
            kwargs.update(name)
            for attr, value in kwargs.iteritems():
                if self._is_format(attr):
                    setattr(self, attr, NameAttr(value, self))
    
    def refresh(self):
        """ Refresh the data from the look up table
        """
        # Setting initial options from config file
        self.format_string = self.cfg.get_subsection_as_str('naming_format', 'format')
        self.suffix_LUT = self.cfg.get_section('suffixes')
        self.subsets = self.cfg.get_subsection_as_list('naming_subsets', 'subsets')
        self.format_options = self.cfg.get_section('naming_format')
        
        # Self parsing
        self.format_order = self.get_format_order(self.format_string)
        if self.camel_case:
            self.format_capitals = self.get_camel_case(self.format_string)
        
        # Setting options for option fields in the UI generated from the config file
        self.side_opt = self.cfg.get_subsection_as_list('options', 'side')
        self.var_opt = self.cfg.get_subsection_as_list('options', 'var')
        self.location_opt = self.cfg.get_subsection_as_list('options', 'location')
        
        self.type_opt = [val for key, val in self.suffix_LUT.iteritems()]
        self.type_opt.sort()
    
    def init_from_suffix_lut(self):
        """ Initialize all the needed attributes for the format order to succeed
        """
        for format_key in self.format_order:
            if not format_key in self.__dict__:
                setattr(self, format_key, NameAttr("", self))
    
    def reset(self, input_dict):
        """ Re-Initialize all the needed attributes for the format order to succeed
        Args:
            kwargs (dict): any overrides the user wants to specify instead of reset to ""
        Returns None
        """
        # Just in case we're working with a string, we assume that's a name
        if isinstance(input_dict, str) or isinstance(input_dict, unicode):
            input_dict = {'name':input_dict}
        
        # Now replace all self.__dict__ attributes to a NameAttr with the given values
        for format_key in self.format_order:
            setattr(self, format_key, NameAttr(input_dict.get(format_key, ""), self))
    
    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        # Need to use deep copy to do a true snapshot of current settings without manipulating them
        dict_buffer = self.get_dict()
        
        # Set whatever the user has specified if it's a valid format token
        for kwarg, value in kwargs.iteritems():
            if self._is_format(kwarg):
                dict_buffer[kwarg] = value
            
        result = self.format_string
        
        for key, attr in dict_buffer.iteritems():
            if key in result:
                token_raw = attr
                if token_raw:
                    replacement = str(token_raw)
                    # Check if the token is an actual suffix (from the UI)
                    if token_raw in [v for k, v in self.suffix_LUT.iteritems()]:
                        replacement = token_raw
                    
                    # Or check through the suffix dictionary for a match
                    elif key == 'type':
                        replacement = self.suffix_LUT.get(token_raw, "")

                    if key in self.format_capitals and self.camel_case:
                        replacement = replacement.title()
                    
                    # Now replace the token with the input
                    result = result.replace('{'+key+'}', replacement)
        
        return self.cleanup_format( result )
        
    def get_dict(self, **kwargs):
        """ Returns a dictionary of relevant attribute values to set a new nomenclate or build a new one
        Args:
            kwargs (dict): any extra definitions you want to input into the resulting dictionary
        Returns (dict): dictionary of relevant values
        """
        # Get every possible NameAttr out of the Nomenclate object
        buffer=[]
        for key, value in self.__dict__.iteritems():
            if self._is_format(key):
                buffer.append(key)
                
        # Now add all dictionary keys that aren't empty to the output dictionary
        output={}
        for key in buffer:
            output[key] = self.__dict__.get(key).get()
        
        # Now add in any extras the user wanted to override
        for key, value in kwargs.iteritems():
            if key in self.format_string and isinstance(value, str):
                output[key] = value
        
        return output
        
    def get_chain(self, end, start=None, **kwargs):
        """ Returns a list of names based on index values
        Args:
            end (int): integer for end of sequence
        Returns (list): generated object names
        """
        var_orig = self.var.get()
        var_start, type = self._detect_type(self.var.get())
        
        # Just in case the start hasn't been overridden it's based on the current var_opt index
        if start==None:
            start = var_start
        names = []
        for index in range(start, end+1):
            if type in ['char_hi','char_lo']:
                capital = True if type == 'char_hi' else False
                self.var.set(self.get_alpha(index, capital))
                
            else:
                self.var.set(str(index))
            if 'var' in kwargs:
                kwargs.pop("var", None)
            names.append(self.get(**kwargs))
        self.var.set(var_orig)
        return names
        
    def get_camel_case(self, format_string):
        """ Returns which tokens need first letter capitalization
        Args:
            formatted_string (string): format_string containing all tokenization
        Returns [string]: list of tokens that need capitalization
        """
        # test = '{side}_{location}_{name}{decorator}J{var}_{childType}_{purpose}_{type}'
        token_sections = format_string.split('_')
        capitalize_firsts = []
        for token_section in token_sections:
            num_tokens = token_section.count('}')
            tokens_ordered = self.get_format_order(token_section)
            if len(tokens_ordered) > 1:
                capitalize_firsts = capitalize_firsts + tokens_ordered[1:]

        return capitalize_firsts
    
    def get_state(self, input_dict=None):
        """ Returns the current state of dictionary items
        """
        if input_dict == None:
            input_dict = self.__dict__
        return ["%s: %s #=%s"%(item, input_dict[item].get(), item.__hash__()) for item in input_dict 
                if isinstance(input_dict[item], NameAttr)]
    
    @staticmethod
    def _detect_type(qstring):
        """ Given an input string of either int or char, returns what index and type it is
        Args:
            qstring (str): query string
        Returns [int, str]: list of the index and type
        """
        try:
            return [int(qstring), 'int']
        except ValueError:
            if qstring.isupper():
                return [string.uppercase.index(qstring), 'char_hi']
            elif qstring.islower():
                return [string.lowercase.index(qstring), 'char_lo']
        return [0, 'char_hi']
    
    def _is_format(self, name):
        """ For quick checking if a key is part of the format order
        Args:
            name (str): a name of a possible attribute for in a nomenclate string
        """
        if name in self.get_format_order(self.format_string):
            return True
        return False
    
    @staticmethod
    def get_format_order(format_string):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
        Returns [string]: list of the matching tokens
        """
        pattern = r'\{(\w*)\}'
        re_matches = re.findall(pattern, format_string)
        return re_matches

    @staticmethod
    def cleanup_format(formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores
        Args:
            formatted_string (string): string that has had tokens replaced
        Returns (string): cleaned up name of object
        """
        # Pattern = r'(?P<word>\{\w*\})|(?P<under>_+)'
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
            
    def switch_naming_format(self, format_target):
        self.format_string = self.get_format_info('naming_format', specific='format')

    @staticmethod
    def get_alpha(value, capital=False):
        """ Convert an integer value to a character. a-z then double aa-zz etc
        Args:
            value (int): integer index we're looking up
        Returns (str): alphanumeric representation of the index
        """
        # calculate number of characters required
        base_power = base_start = base_end = 0
        while value >= base_end:
            base_power += 1
            base_start = base_end
            base_end += pow(26, base_power)
        base_index = value - base_start
        
        # create alpha representation
        alphas = ['a'] * base_power
        for index in range(base_power - 1, -1, -1):
            alphas[index] = chr(97 + (base_index % 26))
            base_index /= 26
            
        if capital:
            return ''.join(alphas).upper()
        return ''.join(alphas)
    
    def __repr__(self):
        return self.get()

class NameParser(object):
    @classmethod
    def rig_nameLong(name):
        pass
        
    @classmethod
    def rig_nameShort(name):
        pass
        
    @classmethod
    def rig_nameGetSide(name):
        pass
        
    @classmethod
    def rig_nameGetBase(name):
        pass
        


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
            raise IOError("Cannot find ini file %s"%self.path)
        try:
            self.parser.get(self.section, self.subsection)
            return True
        except:
            print "Section %s and subsection %s do not exist"%(self.section, self.subsection)
        
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
