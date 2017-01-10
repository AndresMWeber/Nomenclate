#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
import collections
import re
import string
import datetime
import dateutil.parser as p
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions


class TokenAttr(object):
    def __init__(self, label=None, token=None):
        self.validate_entries(label, token)
        self.label = label if label is not None else ""
        self.token = token.lower() if label is not None else ""

    def get(self):
        return self.label

    def set(self, label):
        self.validate_entries(label)
        self.label = label

    @staticmethod
    def validate_entries(*entries):
        for entry in entries:
            if isinstance(entry, str) or entry is None:
                continue
            else:
                raise exceptions.ValidationError('Invalid type %s, expected %s' % (type(entry), str))

    def __eq__(self, other):
        return self.token == other.token and self.label == other.label

    def __repr__(self):
        return '%s:%s' % (self.token, self.label)


class TokenAttrDictHandler(dict):
    def __init__(self, nomenclate_object):
        super(dict, self).__init__()
        self.nom = nomenclate_object

    @property
    def state(self):
        return dict((name_attr.token, name_attr.label) for name_attr in self.get_token_attrs())

    @state.setter
    def state(self, input_object, **kwargs):
        """
        Args:
            input_object Union[dict, self.__class__]: accepts a dictionary or self.__class__
        """
        if isinstance(input_object, self.nom.__class__):
            input_object = input_object.state

        elif not isinstance(input_object, dict):
            raise exceptions.FormatError('state setting only accepts type %s, not given input %s %s' %
                                         (dict, input_object, type(input_object)))

        print ('updating state with input dicts', input_object, kwargs)
        self.set_token_attrs(combine_dicts(input_object, kwargs))

    def build_name_attrs(self):
        """ Creates all necessary name attributes for the naming convention
        """
        self.purge_invalid_name_attrs()
        self.set_token_attrs({token: "" for token in self.nom.format_order})

    def purge_invalid_name_attrs(self):
        """ Removes name attrs not found in the format order
        """
        for token_attr in list(self.get_token_attrs()):
            try:
                self._validate_name_in_format_order(token_attr.label, self.nom.format_order)
            except exceptions.FormatError:
                del self[token_attr.token]

    def purge_name_attrs(self):
        for token_attr in list(self.get_token_attrs()):
            del self[token_attr.token]
        self.update_nomenclate_token_attributes()

    def clear_name_attrs(self):
        for token_attr in self.get_token_attrs():
            token_attr.set('')

    def set_token_attrs(self, input_dict):
        for input_attr_name, input_attr_value in iteritems(input_dict):
            self.set_token_attr(input_attr_name, input_attr_value)
        self.update_nomenclate_token_attributes()

    def set_token_attr(self, token, value):
        token_attrs = list(self.get_token_attrs())
        if token not in [token_attr.token for token_attr in token_attrs]:
            self._create_token_attr(token, value)
        else:
            for token_attr in token_attrs:
                if token == token_attr.token:
                    token_attr.label = value
                    break

    def get_token_attrs(self):
        for name, value in iteritems(self):
            if isinstance(value, TokenAttr):
                yield value

    def get_token_attr(self, token):
        token_attr = getattr(self, token.lower())
        if token_attr is None:
            raise exceptions.SourceError('This nomenclate instance has no %s attribute set.' % token)
        else:
            return token_attr

    def get_token_values_dict(self):
        return dict([(attr.token, attr.label) for attr in self.get_token_attrs()])

    def _create_token_attr(self, token, value):
        self[token.lower()] = TokenAttr(label=value, token=token)

    def get_unset_token_attrs(self):
        return [token_attr for token_attr in self.get_token_attrs()
                if token_attr.label == '']

    def update_state(self, merge_dict):
        self.state = merge_dict

    def update_nomenclate_token_attributes(self):
        for token_attribute in self.get_token_attrs():
            setattr(self.nom, token_attribute.token, token_attribute)

    def clear_nomenclate_excess_token_attributes(self):
        for token_attr_key, token_attr_object in self.get_nomenclate_token_attributes():
            if token_attr_key not in self.nom.format_order:
                delattr(self.nom, token_attr_key)

    def get_nomenclate_token_attributes(self):
        return [(attr, value) for attr, value in iteritems(self.nom.__dict__) if isinstance(value, TokenAttr)]

    @staticmethod
    def _validate_name_in_format_order(name, format_order):
        """ For quick checking if a key token is part of the format order
        """
        if name not in [token.lower() for token in format_order]:
            raise exceptions.FormatError('The name token %s is not found in the current format ordering' %
                                         format_order)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(map(lambda x: x[0] == x[1], zip(self.get_token_attrs(), other.get_token_attrs())))
        return False

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            object.__getattribute__(self, name)

    def __repr__(self):
        return ' '.join(['%s:%s' % (token_attr.token, token_attr.label) for token_attr in self.get_token_attrs()])


class Nomenclative(object):
    def __init__(self, input_str):
        self.str = input_str
        self.token_matches = []

    def process_matches(self):
        build_str = self.str
        for token_match in self.token_matches:
            print(build_str[token_match.start:token_match.end])
            if token_match.match == build_str[token_match.start:token_match.end]:
                print(build_str)
                build_str = build_str[:token_match.start] + token_match.sub + build_str[token_match.end:]
                print('matched!!!')
                print(build_str)
                self.adjust_other_matches(token_match)
        return build_str

    def adjust_other_matches(self, adjuster_match):
        for token_match in [token_match for token_match in self.token_matches if token_match != adjuster_match]:
            try:
                token_match.adjust_position(adjuster_match)
            except IndexError:
                pass

    def add_match(self, regex_match, substitution):
        token_match = TokenMatch(regex_match, substitution)
        try:
            self.validate_match(token_match)
            self.token_matches.append(token_match)
        except IndexError:
            print('Not adding match %s as it conflicts with a preexisting match' % token_match)

    def validate_match(self, token_match_candidate):
        for token_match in self.token_matches:
            if token_match.overlaps(token_match_candidate):
                raise IndexError('Match with range %d-%d overlaps with an existing match with range %d-%d' %
                                 (token_match_candidate.start, token_match_candidate.end, token_match.start, token_match.end))

    def __repr__(self):
        return self.str

    def __str__(self):
        return self.str


class TokenMatch(object):
    def __init__(self, regex_match, substitution, group_name='token'):
        self.match = regex_match.group(group_name)
        self.start = regex_match.start(group_name)
        self.end = regex_match.end(group_name)
        self.sub = substitution
        self.span = self.end - self.start

    def adjust_position(self, other, adjust_by_sub_delta=True):
        if isinstance(other, self.__class__):
            if not other.overlaps(self) and self > other:
                adjustment = other.span - len(other.sub) if adjust_by_sub_delta else other.span
                self._adjust_order(adjustment)
            else:
                raise IndexError('Current TokenMatch overlaps with input TokenMatch\n\t%s\n\t%s' % (repr(self), repr(other)))
        else:
            raise IOError('Only TokenMatch objects are valid inputs to adjust_position')

    def _adjust_order(self, adjust_value):
        self.start -= adjust_value
        self.end -= adjust_value

    def overlaps(self, other):
        return self in other or other in self

    def __contains__(self, other):
        try:
            return (self.start < other.start < self.end or self.start < other.end < self.end)
        except:
            raise NotImplementedError(
                '{C} objects do not handle in syntax for non class objects'.format(C=self.__class__.__name__))

    def __eq__(self, other):
        try:
            return (self.start == other.start and self.end == other.end and
                    self.match == other.match and self.sub == other.sub)
        except:
            raise NotImplementedError(
                '{C} objects do not handle == syntax for non class objects'.format(C=self.__class__.__name__))

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.end <= other.start
        else:
            raise NotImplementedError

    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.start >= other.end
        else:
            raise NotImplementedError

    def __repr__(self):
        return '%s (%d)- [%d:%d] - replacement = %s' % (self.match, self.span, self.start, self.end, self.sub)


class InputRenderer(object):
    @classmethod
    def render_nomenclative(cls, nomenclate_object):
        nomenclative = Nomenclative(nomenclate_object.format_string)
        token_values = nomenclate_object.token_dict.get_token_values_dict()
        # print ('token_values', token_values)
        cls.render_unique_tokens(nomenclate_object, token_values)
        # print ('token values rendered', token_values)
        rendered_nomenclative = nomenclate_object.format_string_object.format_string
        # print ('formatting start', rendered_nomenclative)

        cls._prepend_token_match_objects(token_values, rendered_nomenclative)

        for token, match_value in iteritems(token_values):
            nomenclative.add_match(*match_value)

        rendered_nomenclative = cls.cleanup_formatted_string(nomenclative.process_matches())
        return rendered_nomenclative

    @classmethod
    def _prepend_token_match_objects(cls, token_values, incomplete_nomenclative):
        for token, value in iteritems(token_values):
            re_token = r'(?P<token>((?<![a-z]){TOKEN})|((?<=[a-z]){TOKEN_CAPITALIZED}))'
            re_token = re_token.format(TOKEN=token,
                                       TOKEN_CAPITALIZED=token[0].upper()+token[1:])
            re_matches = re.finditer(re_token, incomplete_nomenclative, 0)

            for re_match in re_matches:
                token_values[token] = (re_match, value)

        cls._clear_non_matches(token_values)

    @staticmethod
    def _clear_non_matches(token_values):
        to_delete = []
        for token, value in iteritems(token_values):
            if isinstance(value, str) or not isinstance(value, tuple):
                to_delete.append(token)

        for delete in to_delete:
            token_values.pop(delete)

    @staticmethod
    def _render_replacements(replacements_dict, incomplete_nomenclative):
        for token, match_value in iteritems(replacements_dict):
            match, value = match_value
            incomplete_nomenclative = incomplete_nomenclative.replace(match, value)

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

    @classmethod
    def render_unique_tokens(cls, nomenclate_object, input_dict):
        print('rendering unique tokens!')
        for k, v in iteritems(input_dict):

            render_method = '_render_%s' % k
            print('checking for custom token method ', render_method)
            try:
                render_method = getattr(cls, render_method)

                if callable(render_method):
                    print('render method found and callable, using to convert!')
                    input_dict[k] = render_method(v, nomenclate_object)

            except AttributeError:
                # TODO: maybe log this?
                pass

    @staticmethod
    def _render_date(date, nomenclate_object):
        if date == 'now':
            d = datetime.datetime.now()
        else:
            try:
                d = p.parse(date)
            except ValueError:
                return ''

        return d.strftime(get_keys_containing(nomenclate_object.__dict__, 'format', '%Y-%m-%d'))

    @staticmethod
    def _render_var(var, nomenclate_object):
        if var:
            return InputRenderer._get_variation_id(get_keys_containing(nomenclate_object.__dict__,
                                                                       'index',
                                                                       0),
                                                   var.isupper())
        else:
            return var

    @staticmethod
    def _render_version(version, nomenclate_object):
        return '%0{0}d'.format(get_keys_containing(nomenclate_object.__dict__, 'padding', 4)) % version

    @staticmethod
    def _render_type(type, nomenclate_object):
        print ('rendering type...')
        return nomenclate_object.get_suffix(type, first=True)

    @staticmethod
    def _get_variation_id(integer, capital=False):
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


class FormatString(object):
    FORMAT_STRING_REGEX = r'([A-Za-z][^A-Z_.]*)'

    def __init__(self, format_string=""):
        self.format_string = format_string
        self.swap_format(format_string)

    def swap_format(self, format_target):
        try:
            self._validate_format_string(format_target)
            self.format_string = format_target
        except exceptions.FormatError:
            pass
        finally:
            self.format_order = self.get_format_order(format_target)

    def get_format_order(self, format_target):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
                http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters
        Returns [string]: list of the matching tokens
        """
        try:
            # TODO: probably needs lots of error checking, need to write a test suite.
            pattern = re.compile(self.FORMAT_STRING_REGEX)
            return pattern.findall(format_target)
        except TypeError:
            raise exceptions.FormatError('Format string %s is not a valid input type, must be <type str>' %
                                         format_target)

    def _validate_format_string(self, format_target):
        """ Checks to see if the target format string follows the proper style
        """
        format_order = self.get_format_order(format_target)
        separators = '\\._-?'

        format_target = format_target.lower()

        for format_str in format_order:
            format_target = format_target.replace(format_str.lower(), '')
        for char in format_target:
            if char not in separators:
                raise exceptions.FormatError("You have specified an invalid format string %s." % format_target)

        # if format_target != '_'.join(format_order):
        #     raise exceptions.FormatError("You have specified an invalid format string %s." % format_target)

    def __str__(self):
        return str(self.format_string)


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

    UNIQUE_TOKENS = ['date', 'var', 'version']

    def __init__(self, *args, **kwargs):
        self.cfg = config.ConfigParse()
        self.token_dict = TokenAttrDictHandler(self)
        self.format_string_object = FormatString()

        self.SUFFIX_OPTIONS = dict()
        self.FORMATS_OPTIONS = dict()
        self.CONFIG_OPTIONS = dict()

        self.reset_from_config()

        print ('args, kwargs init', args, kwargs)
        self.merge_dict(*args, **kwargs)
        print('init state', self.state)

    @property
    def tokens(self):
        return list(self.token_dict.state)

    @property
    def format_order(self):
        return self.format_string_object.format_order

    @property
    def state(self):
        return self.token_dict.state

    @state.setter
    def state(self, input_object):
        """
        Args:
            input_object Union[dict, self.__class__]: accepts a dictionary or self.__class__
        """
        input_object = self._convert_input(input_object)
        self.token_dict.state = input_object

    @property
    def format_string(self):
        return str(self.format_string_object)

    @format_string.setter
    def format_string(self, format_target):
        self.format_string_object.swap_format(format_target)

    def reset_from_config(self):
        self.initialize_config_settings()
        self.initialize_format_options()
        self.initialize_options()
        self.initialize_ui_options()

    def initialize_config_settings(self, input_dict=None):
        input_dict = input_dict or self.cfg.get(self.CONFIG_PATH, return_type=dict)
        for setting, value in iteritems(input_dict):
            setattr(self, setting, value)

    def initialize_format_options(self, format_target=''):
        """ First attempts to use format_target as a config path or gets the default format
            if it's invalid or is empty.
        Args:
            format_target Union[str, list]: can be either a query path to a format
                                            or in format of a naming string the sections should be spaced around
                                              e.g. - this_is_a_naming_string
        Returns None: raises IOError if failure
        """
        try:
            format_path = format_target if isinstance(format_target, list) else [format_target]
            format_target = self.cfg.get(format_path, return_type=str)

        except exceptions.ResourceNotFoundError:
            format_target = format_target or self.cfg.get(self.DEFAULT_FORMAT_PATH, return_type=str)

        finally:
            self.format_string_object.swap_format(format_target)
            self.token_dict.build_name_attrs()

    def initialize_options(self):
        self.FORMATS_OPTIONS = self.cfg.get(self.NAMING_FORMAT_PATH, return_type=dict)
        self.CONFIG_OPTIONS = self.cfg.get(self.CONFIG_PATH, return_type=dict)
        self.SUFFIX_OPTIONS = self.cfg.get(self.SUFFIXES_FORMAT_PATH, return_type=dict)

    def initialize_ui_options(self):
        """
        Placeholder for all categories/sub-lists within options to be recorded here
        """
        pass

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        print('\n\n\ngetting!!!!!')
        self.merge_dict(**kwargs)
        result = InputRenderer.render_nomenclative(self)
        result = InputRenderer.cleanup_formatted_string(result)
        return result

    def get_chain(self, end, start=None, **kwargs):
        """ Returns a list of names based on index values
        Args:
            end (int): integer for end of sequence
            start (int): optional definition of start position
        Returns (list): generated object names
        """
        # TODO: rework this entire function, very dirty function.
        var_attr = self.token_dict.get_token_attr(self.VARIATION_PATH[-1])
        var_orig = var_attr.get()

        var_start, n_type = self._get_alphanumeric_index(var_orig)

        if start is None:
            start = var_start
        names = []
        for index in range(start, end + 1):
            if n_type in ['char_hi', 'char_lo']:
                capital = True if n_type == 'char_hi' else False
                var_attr.set(self._get_variation_id(index, capital))

            else:
                var_attr.set(str(index))
            if 'var' in kwargs:
                kwargs.pop("var", None)
            names.append(self.get(**kwargs))
        var_attr.set(var_orig)
        return names

    def get_unset_tokens(self):
        return self.token_dict.get_unset_token_attrs()

    def merge_dict(self, *args, **kwargs):
        print('entered merge_dict')
        print('state before merge', self.state)
        self.state = combine_dicts(*args, **kwargs)
        print('state after merge', self.state)

    def get_suffix(self, type, first=False):
        matches = gen_dict_extract(type, self.SUFFIX_OPTIONS)
        matches = matches or type
        return matches if not first else list(matches)[0]

    def _convert_input(self, *args, **kwargs):
        print('entered convert_input')
        input_dict = combine_dicts(*args, **kwargs)
        print('convert input after  combine', input_dict)
        self._sift_and_init_configs(input_dict)
        print('convert input end', input_dict)
        return input_dict

    def _sift_and_init_configs(self, input_dict):
        """ Removes all key/v for keys that exist in the overall config and activates them.
            Used to weed out config keys from tokens in a given input.
        """
        print('entered sift_and_init_configs')
        print ('sift start', input_dict)
        configs = {}

        for k, v in iteritems(input_dict):
            try:
                self.cfg.get(self.CONFIG_PATH + [k])
                input_dict.pop(k, None)
                configs[k] = v
            except exceptions.ResourceNotFoundError:
                pass
        print ('sift end', input_dict)
        self.initialize_config_settings(input_dict=configs)

    def __eq__(self, other):
        return self.token_dict == other.token_dict

    def __repr__(self):
        return self.get()


def combine_dicts(*args, **kwargs):
    print ('combine dicts', args, kwargs)
    for arg in args:
        print('arg', arg)
    dicts = [arg for arg in args if isinstance(arg, dict)]
    dicts.append(kwargs)
    super_dict = collections.defaultdict(dict)

    for d in dicts:
        for k, v in iteritems(d):
            if k and v:
                super_dict[k] = v

    print('combined dicts', dict(super_dict))
    return dict(super_dict)


def gen_dict_extract(key, var):
    """
    Yanked from here:
        http://stackoverflow.com/questions/9807634/find-all-occurences-of-a-key-in-nested-python-dictionaries-and-lists
    """
    if isinstance(var, collections.Iterable):
        for k, v in iteritems(var):
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result


def get_keys_containing(input_dict, search_string, default=None, first_found=True):
        output = {}
        for k, v in iteritems(input_dict):
            if search_string in k and not callable(k):
                output[k] = v

        if first_found:
            try:
                output = next(iter(output))
            except StopIteration:
                pass

        output = output or default


        return output
