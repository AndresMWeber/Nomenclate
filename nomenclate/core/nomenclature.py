#!/usr/bin/env python
# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
import re
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions
from nomenclate.core.nomenclative import (
    InputRenderer
)
from nomenclate.core.nlog import (
    getLogger,
    DEBUG,
    INFO
)
from nomenclate.core.tools import (
    combine_dicts
)


class TokenAttr(object):
    LOG = getLogger(__name__, level=DEBUG)

    def __init__(self, label=None, token=None):
        self.validate_entries(label, token)
        self.raw_string = label if label is not None else ""
        self.raw_token = token

    @property
    def token(self):
        return self.raw_token.lower()

    @token.setter
    def token(self, token):
        self.validate_entries(token)
        self.raw_token = token

    @property
    def label(self):
        return self.raw_string

    @label.setter
    def label(self, label):
        self.validate_entries(label)
        self.LOG.debug('Setting token attr %s -> %r' % (str(self), label))
        self.raw_string = label
        self.LOG.debug('%s and the raw_string is %s' % (self, self.raw_string))

    def set(self, value):
        self.label = value

    @staticmethod
    def validate_entries(*entries):
        for entry in entries:
            if isinstance(entry, str) or entry is None:
                continue
            else:
                raise exceptions.ValidationError('Invalid type %s, expected %s' % (type(entry), str))

    def __eq__(self, other):
        return self.token == other.token and self.label == other.label

    def __str__(self):
        return '%s(%s):%r' % (self.token, self.raw_token, self.label)


class TokenAttrDictHandler(object):
    LOG = getLogger(__name__, level=DEBUG)

    def __init__(self, nomenclate_object):
        self.nom = nomenclate_object
        self.set_token_attrs({})

    @property
    def token_attrs(self):
        return self.gen_object_token_attributes(self)

    @property
    def state(self):
        return dict((name_attr.token, name_attr.label) for name_attr in self.token_attrs)

    @state.setter
    def state(self, input_object, **kwargs):
        """
        Args:
            input_object Union[dict, self.__class__]: accepts a dictionary or self.__class__
        """
        self.set_token_attrs(self.nom._convert_input(input_object, kwargs))

    @property
    def empty_state(self):
        return {token: "" for token in self.nom.format_order}

    @property
    def unset_token_attrs(self):
        return [token_attr for token_attr in self.token_attrs if token_attr.label == '']

    @property
    def token_attr_dict(self):
        return dict([(attr.token, attr.label) for attr in self.token_attrs])

    def purge_invalid_name_attrs(self):
        """ Removes name attrs not found in the format order
        """
        token_attrs = list(self.token_attrs)
        self.LOG.debug('Checking if current TokenAttrs %s are in format order %s' % (map(str, token_attrs),
                                                                                     self.nom.format_order))
        for token_attr in token_attrs:
            try:
                self._validate_name_in_format_order(token_attr.raw_token, self.nom.format_order)
            except exceptions.FormatError:
                self.LOG.debug('Deleting invalid TokenAttr %s' % token_attr.token)
                del self.__dict__[token_attr.token]

    def reset(self):
        for token_attr in self.token_attrs:
            token_attr.set('')

    def set_token_attrs(self, input_dict):
        self.LOG.info('Setting token attributes %s' % input_dict)
        defaults = self.empty_state
        defaults.update(input_dict)
        self.LOG.debug('Filled in empty settings %s' % defaults)

        for input_attr_name, input_attr_value in iteritems(defaults):
            self.set_token_attr(input_attr_name, input_attr_value)

        self.LOG.debug('Finished setting attributes on TokenDict %s' % map(str, list(self.token_attrs)))
        self.purge_invalid_name_attrs()
        self.update_nomenclate_token_attributes()

    def set_token_attr(self, token, value):
        self.LOG.info('set_token_attr() - Setting TokenAttr %s with value %r' % (token, value))
        token_attrs = list(self.token_attrs)

        if token not in [token_attr.raw_token for token_attr in token_attrs]:
            self.LOG.debug('Token did not exist, creating...')
            self._create_token_attr(token, value)
        else:
            for token_attr in token_attrs:
                self.LOG.debug('Checking if token %r is equal to preexisting token %r' % (token, token_attr.token))
                if token == token_attr.token:
                    self.LOG.debug('Found matching token, setting value to %r' % value)
                    token_attr.label = value
                    break

    def get_token_attr(self, token):
        token_attr = getattr(self, token.lower())
        if token_attr is None:
            self.LOG.error(exceptions.SourceError('Instance has no %s token attribute set.' % token), exc_info=True)
        else:
            return token_attr

    def _create_token_attr(self, token, value):
        self.LOG.debug('_create_token_attr(%s:%s)' % (token, repr(value)))
        self.__dict__[token.lower()] = TokenAttr(label=value, token=token)

    def update_nomenclate_token_attributes(self):
        token_attrs = list(self.token_attrs)
        self.LOG.info('Updating nomenclate attributes - %s' % map(str, token_attrs))
        for token_attribute in token_attrs:
            setattr(self.nom, token_attribute.token, token_attribute)
        self.LOG.info('Clearing unused tokens...')
        self.clear_nomenclate_excess_token_attributes()
        self.LOG.info('Finished updating Nomenclate object.')

    def clear_nomenclate_excess_token_attributes(self):
        for token_attr in self.gen_object_token_attributes(self.nom):
            if token_attr.raw_token not in self.nom.format_order:
                self.LOG.info('Deleting unsynchronized Nomenclate TokenAttr' % token_attr.token)
                delattr(self.nom, token_attr.token)

    @staticmethod
    def gen_object_token_attributes(object):
        for name, value in iteritems(object.__dict__):
            if isinstance(value, TokenAttr):
                yield value

    @staticmethod
    def _validate_name_in_format_order(name, format_order):
        """ For quick checking if a key token is part of the format order
        """
        if name not in format_order:
            raise exceptions.FormatError('The name token %s is not found in the current format ordering' %
                                         format_order)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(map(lambda x: x[0] == x[1], zip(self.token_attrs, other.token_attrs)))
        return False

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            object.__getattribute__(self.__dict__, name)

    def __str__(self):
        return ' '.join(['%s:%s' % (token_attr.token, token_attr.label) for token_attr in self.token_attrs])


class FormatString(object):
    # FORMAT_STRING_REGEX = r'([A-Za-z][^A-Z_.]*)'
    FORMAT_STRING_REGEX = r'(?:(?<=\()[\w]+(?=\)))|([A-Za-z0-9][^A-Z_.\(\)]+)'
    SEPARATORS = '\\._-?()'

    LOG = getLogger(__name__, level=DEBUG)

    def __init__(self, format_string=""):
        self.format_string = format_string
        self.format_order = format_string
        self.swap_format(format_string)

    def swap_format(self, format_target):
        try:
            self.format_order = format_target
            self.format_string = format_target
            self.LOG.info('Successfully set format string: %s and format order: %s' % (self.format_string,
                                                                                       self.format_order))
        except exceptions.FormatError as e:
            msg = "Could not validate input format target %s"
            self.LOG.error('%s, %s' % (msg, e.message))

    def parse_format_order(self, format_target):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
                http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters
        Returns [string]: list of the matching tokens
        """
        self.LOG.debug('Getting format order from target %s' % repr(format_target))
        try:
            pattern = re.compile(self.FORMAT_STRING_REGEX)
            return [match.group() for match in pattern.finditer(format_target) if None not in match.groups()]
        except TypeError:
            raise exceptions.FormatError('Format string %s is not a valid input type, must be <type str>' %
                                         format_target)

    @property
    def format_order(self):
        return self.processed_format_order

    @format_order.setter
    def format_order(self, format_target):
        if format_target:
            self.processed_format_order = self.get_valid_format_order(format_target,
                                                                      format_order=self.parse_format_order(format_target))
        else:
            self.processed_format_order = []

    def get_valid_format_order(self, format_target, format_order=None):
        """ Checks to see if the target format string follows the proper style
        """
        self.LOG.debug('Validating format string and parsing for format order.')
        format_order = format_order or self.parse_format_order(format_target)

        for format_str in format_order:
            format_target = format_target.replace(format_str, '')

        for char in format_target:
            if char not in self.SEPARATORS:
                msg = "You have specified an invalid format string %s." % format_target
                self.LOG.warning(msg)
                raise exceptions.FormatError(msg)
        return format_order

    def __str__(self):
        return str(self.format_string)


class Nomenclate(object):
    """This class deals with renaming of objects in an approved pattern
    """
    LOG = getLogger(__name__, level=INFO)
    CONFIG_PATH = ['overall_config']

    NAMING_FORMAT_PATH = ['naming_formats']
    DEFAULT_FORMAT_PATH = NAMING_FORMAT_PATH + ['node', 'default']

    SUFFIXES_PATH = ['suffixes']
    OPTIONS_PATH = ['options']
    SIDE_PATH = OPTIONS_PATH + ['side']

    def __init__(self, logger=None, *args, **kwargs):
        self.cfg = config.ConfigParse()
        self.format_string_object = FormatString()

        self.CONFIG_OPTIONS = dict()

        self.reset_from_config()
        self.token_dict = TokenAttrDictHandler(self)
        self.merge_dict(*args, **kwargs)

    @property
    def empty_tokens(self):
        return self.token_dict.unset_token_attrs

    @property
    def tokens(self):
        return list(self.token_dict.state)

    @property
    def format_order(self):
        return self.format_string_object.format_order

    @property
    def state(self):
        print(self.token_dict.var)
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
    def format(self):
        return str(self.format_string_object)

    @format.setter
    def format(self, format_target):
        self.LOG.info('Attempting to swap format to target %s' % format_target)
        try:
            self.format_string_object.swap_format(format_target)
        except exceptions.FormatError:
            self.LOG.info('Format target is not a valid format string, looking in config for: %s' % format_target)
            format_target = self.cfg.get(format_target, return_type=str)
            if format_target:
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
        return_type = str
        self.LOG.info('initialize_format_options with %s' % repr(format_target))
        try:
            format_target = self.cfg.get(format_target, return_type=return_type)

        except (exceptions.ResourceNotFoundError, StopIteration):
            pass

        finally:
            if not format_target:
                self.LOG.debug('Format not found, replacing with default format from config path %s' %
                               self.DEFAULT_FORMAT_PATH)
                format_target = self.cfg.get(self.DEFAULT_FORMAT_PATH, return_type=return_type)

            self.LOG.info('format target is now %s after looking in the config for a match' % format_target)
            self.format = format_target

    def initialize_options(self):
        self.CONFIG_OPTIONS = self.cfg.get(self.CONFIG_PATH, return_type=dict)

    def initialize_ui_options(self):
        """
        Placeholder for all categories/sub-lists within options to be recorded here
        """
        pass

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
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
        """
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
        """
        raise NotImplementedError

    def merge_dict(self, *args, **kwargs):
        input = self._convert_input(*args, **kwargs)
        self.state = self._sift_and_init_configs(input)

    def _convert_input(self, *args, **kwargs):
        args = [arg.state if isinstance(arg, Nomenclate) else arg for arg in args]
        input_dict = combine_dicts(*args, **kwargs)
        return input_dict

    def _sift_and_init_configs(self, input_dict):
        """ Removes all key/v for keys that exist in the overall config and activates them.
            Used to weed out config keys from tokens in a given input.
        """
        configs = {}
        to_pop = []
        for k, v in iteritems(input_dict):
            try:
                self.cfg.get(self.CONFIG_PATH + [k])
                to_pop.append(k)
                configs[k] = v
            except exceptions.ResourceNotFoundError:
                pass

        for pop in to_pop:
            input_dict.pop(pop, None)

        self.initialize_config_settings(input_dict=configs)

    def __eq__(self, other):
        return self.token_dict == other.token_dict

    def __str__(self):
        return self.get()

    def __setattr__(self, key, value):
        attr = getattr(self, key, None)
        if isinstance(attr, TokenAttr):
            attr.label = value.label if isinstance(value, TokenAttr) else value
            self.LOG.debug('User setting TokenAttr %s to %s, now is %s' % (attr, value, attr.label))
        else:
            self.LOG.debug('User setting attribute %s to %s' % (key, value))
            object.__setattr__(self, key, value)
