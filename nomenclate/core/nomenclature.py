#!/usr/bin/env python
from six import iteritems

import nomenclate.settings as settings
from . import configurator as config
from . import errors
from . import tokens
from . import formatter
from . import rendering
from .tools import (
    combine_dicts,
    NomenclateNotifier
)

MODULE_LOGGER_LEVEL_OVERRIDE = settings.QUIET


class Nomenclate(object):
    """This class deals with renaming of objects in an approved pattern
    """
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)
    CONFIG_PATH = ['overall_config']

    NAMING_FORMAT_PATH = ['naming_formats']
    DEFAULT_FORMAT_PATH = NAMING_FORMAT_PATH + ['node', 'default']

    SUFFIXES_PATH = ['suffixes']
    OPTIONS_PATH = ['options']
    SIDE_PATH = OPTIONS_PATH + ['side']

    def __init__(self, input_dict=None, format_string='', config_filepath='env.yml', *args, **kwargs):
        """

        :param input_dict: dict, In case the user just passes a dictionary as the first arg in the init, we will merge it.
        :param format_string: str, input format string
        :param config_filepath: str, filepath, full or relative to a config file
        :param args: dict, any amount of dictionaries desired as input
        :param kwargs: str, kwargs to pass to the nomenclate tokens
        """
        input_dict = dict() if input_dict is None else input_dict

        self.notifier = NomenclateNotifier(self.__setattr__)
        self.LOG.info('***CREATING NEW NOMENCLATE OBJECT***')
        self.LOG.info('Nomenclate init passed args %s and kwargs %s...processing' % (args, kwargs))

        self.cfg = config.ConfigParse(config_filepath=config_filepath)
        self.format_string_object = formatter.FormatString(format_string=format_string)
        self.CONFIG_OPTIONS = dict()

        self.reset_from_config(format_target=format_string)
        self.token_dict = tokens.TokenAttrDictHandler(self)

        self.merge_dict(input_dict, *args, **kwargs)
        self._update_tokens()

    @property
    def empty_tokens(self):
        return {token.token: token.label for token in self.token_dict.unset_token_attrs}

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
        """ Property setter used to integrate new settings

        :param input_object: (dict, Nomenclate): input dictionary/instance to integrate
        :return: None
        """
        self.merge_dict(input_object)

    @property
    def format(self):
        return str(self.format_string_object)

    @format.setter
    def format(self, format_target, remove_obsolete_tokens=True):
        """ Changes the internal self.format_string_object format target based on input.  Also checks to see if input
            is an entry in the config file in case we want to switch to a preexisting config format.

        :param format_target: str, input for the new format type.  All strings will be the new tokens.
        :param remove_obsolete_tokens: bool, dictates whether we are removing the obselete tokens or not that
               previously existed
        :return: None
        """
        self.LOG.info('Attempting to swap format to target %r' % format_target)
        original_format, original_format_order = (self.format, self.format_order)

        try:
            self.LOG.info('Looking in config for format target: %r' % format_target)
            format_target = self.cfg.get(format_target, return_type=str, throw_null_return_error=True)
            self.LOG.info('Found entry: %r' % format_target)
        except (errors.ResourceNotFoundError, KeyError):
            pass

        self.LOG.info('Format target not found in config, validating as a format string...')
        self.format_string_object.swap_format(format_target)
        self._update_tokens_from_swap_format(original_format,
                                             original_format_order,
                                             remove_obsolete_tokens=remove_obsolete_tokens)

    def reset_from_config(self, format_target=''):
        self.LOG.info('Starting reset')
        self.initialize_config_settings()
        self.initialize_format_options(format_target=format_target)
        self.initialize_options()
        self.initialize_ui_options()

    def initialize_config_settings(self, input_dict=None):
        self.LOG.info('\tinitialize_config_settings with dict %s' % input_dict)
        input_dict = self.cfg.get(self.CONFIG_PATH, return_type=dict) if input_dict is None else input_dict
        for setting, value in iteritems(input_dict):
            setattr(self, setting, value)
            self.LOG.info('\tNew config value <%s>.%s=%r' % (self.__class__.__name__, setting, getattr(self, setting)))

    def initialize_format_options(self, format_target=''):
        """ First attempts to use format_target as a config path or gets the default format
            if it's invalid or is empty.

        :param format_target: (str, list(str)), can be either a query path to a format
                                                or in format of a naming string the sections should be spaced around
                                                e.g. - this_is_a_naming_string
        :raises: IOError
        """
        self.LOG.info('\tinitialize_format_options: format target=%r' % format_target)
        try:
            if format_target:
                self.format = format_target
                self.LOG.info('\t\tSuccessfully set format target.')
            else:
                raise errors.FormatError
        except errors.FormatError:
            format_target = self.cfg.get(self.DEFAULT_FORMAT_PATH, return_type=str)
            self.LOG.info('\t\tFormat not found, replacing with default format from config path %s: %s' %
                          (self.DEFAULT_FORMAT_PATH, format_target))
            self.format_string_object.swap_format(format_target)

        self.LOG.info('\t\tFormat target is now %s after looking in the config for a match' % format_target)

    def initialize_options(self):
        """ Stores options from the config file

        """
        self.LOG.info('\tinitialize_options')
        self.CONFIG_OPTIONS = self.cfg.get(self.CONFIG_PATH, return_type=dict)

    def initialize_ui_options(self):
        """ Placeholder for all categories/sub-lists within options to be recorded here

        """
        self.LOG.info('\tinitialize_ui_options')
        return self.format

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        old_state = self.state.copy()
        self.LOG.info('RENDERING NOMENCLATE OBJECT')
        self.LOG.info('STATE IS: %s' % self.state)
        self.merge_dict(kwargs)
        self.LOG.info('STATE IS: %s' % self.state)
        result = rendering.InputRenderer.render_nomenclative(self)
        self.merge_dict(old_state)
        return result

    def get_chain(self, end, start=None, **kwargs):
        """ Returns a list of names based on index values

        :param end: int, integer for end of sequence
        :param start: (int, optional definition of start position
        :return: list(str), generated object names
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
        """ Takes variable inputs, compiles them into a dictionary then merges it to the current nomenclate's state

        :param args: (dict, Nomenclate), any number of dictionary inputs or Nomenclates to be converted to dicts
        :param kwargs: str, any number of kwargs that represent token:value pairs
        """
        input_dict = self._convert_input(*args, **kwargs)
        self._sift_and_init_configs(input_dict)
        self.LOG.info('Done sifting, now input is %s' % input_dict)
        self.LOG.info('Starting merge, state is %s' % self.token_dict.state)
        self.token_dict.state = input_dict
        self.LOG.info('Finished merge, state is %s' % self.token_dict.state)

    def get_token_settings(self, token, default=None):
        """ Get the value for a specific token as a dictionary or replace with default

        :param token: str, token to query the nomenclate for
        :param default: object, substitution if the token is not found
        :return: (dict, object, None), token setting dictionary or default
        """
        setting_dict = {}

        for key, value in iteritems(self.__dict__):
            if '%s_' % token in key and not callable(key) and not isinstance(value, tokens.TokenAttr):
                setting_dict[key] = self.__dict__.get(key, default)
        return setting_dict

    def _update_tokens(self, specific_tokens=None):
        """ Synchronizes all nomenclate token attributes with values from the token_dict

        :param specific_tokens: list(str): list of tokens to update, otherwise updates all tokens
        """
        self.LOG.info('Force Updating all TokenAttrs')
        if hasattr(self, 'token_dict'):
            specific_tokens = specific_tokens if specific_tokens is not None else list(self.token_dict.state)

            self.LOG.info('Updating nomenclate with %s' % specific_tokens)
            state = {token: getattr(self.token_dict, token) for token in specific_tokens}

            self.LOG.info('Updating nomenclate attributes with state %s' % state)

            for token, token_attr_instance in iteritems(state):
                setattr(self, token, token_attr_instance)

            self.LOG.info('Finished updating Nomenclate object and token_dict.')

    def _purge_tokens(self, token_attrs):
        """ Removes specified token attrs from the instance and from the instance's token_dict to keep synchronized

        :param token_attrs: list(str), list of token attributes to remove
        :return: None
        """
        self.token_dict.purge_tokens(token_attrs)

        for token_attr in token_attrs:
            self.LOG.info('Purging nomenclate attribute - %s' % str(token_attr))
            delattr(self, token_attr)

        self.LOG.info('Finished purging Nomenclate object and token_dict.')

    def _update_tokens_from_swap_format(self, original_format, original_format_order, remove_obsolete_tokens=True):
        """ Updates tokens based on a swap format call that will maintain synchronicity between token_dict and attrs
            If there was an accidental setting already set to one of the attrs that should now be a token attr due
            to the format swap, we wipe it and add a new TokenAttr to the Nomenclate attribute.

        :param original_format: str, original format string to compare to
        :param original_format_order: list(str), the original format order to compare to
        :param remove_obsolete_tokens: bool, whether to remove obsolete tokens
                                             if off: persistent state across format swaps of missing tokens
        """
        old_format_order = [_.lower() for _ in original_format_order]
        new_format_order = [_.lower() for _ in self.format_order]
        if hasattr(self, 'token_dict') and self.format != original_format:
            self.LOG.info('Comparing new format order %s with old format order %s' % (new_format_order,
                                                                                      old_format_order))

            old_tokens = [token for token in list(set(old_format_order) - set(new_format_order))
                          if hasattr(self, token)]

            new_tokens = [token for token in set(new_format_order) - set(old_format_order)
                          if not hasattr(self, token) or isinstance(getattr(self, token, ''), str)]

            self.LOG.info('\nToken Status:\n\tObselete tokens: %s\n\tNew tokens: %s' % (old_tokens, new_tokens))

            self.merge_dict(dict.fromkeys(new_tokens, ''))
            if remove_obsolete_tokens:
                self._purge_tokens(old_tokens)
        else:
            self.LOG.info('No change necessary to update internal token set')

    def _convert_input(self, *args, **kwargs):
        """ Takes variable inputs

        :param args: (dict, Nomenclate), any number of dictionary inputs or Nomenclates to be converted to dicts
        :param kwargs: str, any number of kwargs that represent token:value pairs
        :return: dict, combined dictionary of all inputs
        """
        self.LOG.info('Converting input args %s and kwargs %s' % (args, kwargs))
        args = [arg.state if isinstance(arg, Nomenclate) else arg for arg in args]
        self.LOG.debug('Args after Nomenclate conversion: %s' % args)
        input_dict = combine_dicts(*args, **kwargs)
        self.LOG.info('Converted to %s' % input_dict)
        return input_dict

    def _sift_and_init_configs(self, input_dict):
        """ Removes all key/v for keys that exist in the overall config and activates them.
            Used to weed out config keys from tokens in a given input.
        """
        self.LOG.info('_sift_and_init_configs() - removing config settings from input %s' % input_dict)
        configs = {}
        for k, v in iteritems(input_dict):
            if (k not in map(str.lower, self.format_order) and
                    any([f_order.lower() in k for f_order in self.format_order])):
                try:
                    self.cfg.get(self.CONFIG_PATH + [k])
                except errors.ResourceNotFoundError:
                    pass
                finally:
                    configs[k] = v

        for key, val in iteritems(configs):
            self.LOG.info('Sifting out found config setting %s:%s' % (key, val))
            input_dict.pop(key, None)

        self.initialize_config_settings(input_dict=configs)

    def __eq__(self, other):
        return self.token_dict == other.token_dict

    def __str__(self):
        return self.get()

    def __setattr__(self, key, value):
        """ Custom setattr to detect whether they are trying to set a token, then updating the token_dict

        """
        self.LOG.info('<%s>.__setattr__(%r, %r)' % (self.__class__.__name__, key, value))
        token_dict_attr = getattr(getattr(self, 'token_dict', None), key, None)
        is_not_value_token_attr = not isinstance(value, tokens.TokenAttr)
        is_token_dict_attr_token_attr = isinstance(token_dict_attr, tokens.TokenAttr)

        if all([hasattr(self, 'token_dict'), is_not_value_token_attr, is_token_dict_attr_token_attr]):
            self.LOG.debug('User setting TokenAttr %r -> %r' % (token_dict_attr, value))
            self.token_dict.set_token_attr(key, value)
            # object.__setattr__(self, key, token_dict_attr)
        else:
            self.LOG.debug('User setting attribute %s to %r' % (key, value))
            object.__setattr__(self, key, value)

    def __dir__(self):
        """ Taken from:
            http://techqa.info/programming/question/15507848/the-correct-way-to-override-the-__dir__-method-in-python

        """

        def get_attrs(obj):
            return obj.__dict__.keys()

        def dir_augment(obj):
            attrs = set()
            if not hasattr(obj, '__bases__'):
                # obj is an instance
                instance_class = obj.__class__
                attrs.update(get_attrs(instance_class))
            else:
                # obj is a class
                instance_class = obj

            for cls in instance_class.__bases__:
                attrs.update(get_attrs(cls))
                attrs.update(dir_augment(cls))
            attrs.update(get_attrs(obj))
            return list(attrs)

        return dir_augment(self)
