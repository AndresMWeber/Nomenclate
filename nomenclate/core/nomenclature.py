#!/usr/bin/env python

from nomenclate.settings import DEFAULT_YML_CONFIG_FILE
from . import configurator as config
from . import errors
from . import tokens
from . import formatter
from . import rendering
from .tools import combine_dicts, Serializable


class Nomenclate(Serializable):
    """This class deals with renaming of objects in an approved pattern
    """

    SERIALIZE_ATTRS = ["format_string_object", "token_dict"]

    CONFIG_ROOT = ["overall_config"]

    NAMING_FORMAT_PATH = ["naming_formats"]
    DEFAULT_FORMAT_PATH = NAMING_FORMAT_PATH + ["node", "default"]

    SUFFIXES_PATH = ["suffixes"]
    OPTIONS_PATH = ["options"]
    SIDE_PATH = OPTIONS_PATH + ["side"]

    CONFIG_OPTIONS = dict()
    CFG = config.ConfigParse(config_filename=DEFAULT_YML_CONFIG_FILE)

    def __init__(self, input_dict: dict = None, format_string: str = "", *args, **kwargs):
        """

        :param input_dict: dict, In case the user just passes a dictionary as the first arg in the init, we will merge it.
        :param format_string: str, input format string
        :param args: dict, any amount of dictionaries desired as input
        :param kwargs: str, kwargs to pass to the nomenclate tokens
        """
        self.format_string_object = formatter.FormatString(format_string=format_string)
        self.initialize_format_options(format_target=format_string)
        self.token_dict = tokens.TokenAttrList(self.format_string_object.format_order)
        self.merge_dict(input_dict or dict(), *args, **kwargs)

    @property
    def empty_tokens(self):
        return {token.token: token.label for token in self.token_dict.unset_token_attrs}

    @property
    def tokens(self):
        return list(self.token_dict)

    @property
    def format_order(self):
        return self.format_string_object.format_order

    @property
    def state(self):
        return self.token_dict.to_json()

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
    def format(self, format_target, remove_obsolete=True):
        """ Changes the internal self.format_string_object format target based on input.  Also checks to see if input
            is an entry in the config file in case we want to switch to a preexisting config format.

        :param format_target: str, input for the new format type.  All strings will be the new tokens.
        :param remove_obsolete: bool, dictates whether we are removing the obselete tokens or not that
               previously existed
        :return: None
        """
        original_format, original_format_order = (self.format, self.format_order)

        try:
            format_target = self.CFG.get(format_target, return_type=str)
        except (errors.ResourceNotFoundError, KeyError):
            pass

        self.format_string_object.swap_format(format_target)
        self._update_tokens_from_swap_format(
            original_format, original_format_order, remove_obsolete=remove_obsolete
        )

    @classmethod
    def set_config(cls, config_data: dict):
        """ Set the config file from a dictionary.
        """
        cls.CFG.set_from_dict(config_data)
        cls.reset_from_config()

    @classmethod
    def reset_from_config(cls):
        cls.initialize_overall_config_settings()
        cls.initialize_options()

    @classmethod
    def initialize_overall_config_settings(cls, input_dict=None):
        input_dict = input_dict or cls.CFG.get(cls.CONFIG_ROOT, return_type=dict)
        for setting, value in input_dict.items():
            setattr(cls, setting, value)

    def initialize_format_options(self, format_target=""):
        """ First attempts to use format_target as a config path or gets the default format
            if it's invalid or is empty.

        :param format_target: (str, list(str)), can be either a query path to a format
                                                or in format of a naming string the sections should be spaced around
                                                e.g. - this_is_a_naming_string
        :raises: IOError
        """
        try:
            if format_target:
                self.format = format_target
            else:
                raise errors.FormatError
        except errors.FormatError:
            self.format_string_object.swap_format(
                self.CFG.get(self.DEFAULT_FORMAT_PATH, return_type=str)
            )

    @classmethod
    def initialize_options(cls):
        """ Stores options from the config file

        """
        cls.CONFIG_OPTIONS = cls.CFG.get(cls.CONFIG_ROOT, return_type=dict)

    def get(self, **kwargs):
        """Gets the string of the current name of the object
        Returns (string): the name of the object
        """
        old_state = self.state.copy()
        self.merge_dict(kwargs)
        result = rendering.InputRenderer.render_nomenclative(self)
        self.merge_dict(old_state)
        return result

    def merge_dict(self, *args, **kwargs):
        """ Takes variable inputs, compiles them into a dictionary then merges it to the current nomenclate's state

        :param args: (dict, Nomenclate), any number of dictionary inputs or Nomenclates to be converted to dicts
        :param kwargs: str, any number of kwargs that represent token:value pairs
        """
        input_dict = self._convert_input(*args, **kwargs)
        if input_dict:
            self._sift_and_init_configs(input_dict)
            self.token_dict.merge_serialization(input_dict)

    @classmethod
    def get_token_settings(cls, token, default=None):
        """ Get the value for a specific token as a dictionary or replace with default

        :param token: str, token to query the nomenclate for
        :param default: object, substitution if the token is not found
        :return: (dict, object, None), token setting dictionary or default
        """
        setting_dict = {}

        for key, value in cls.__dict__.items():
            if (
                "%s_" % token in key
                and not callable(key)
                and not isinstance(value, tokens.TokenAttr)
            ):
                setting_dict[key] = cls.__dict__.get(key, default)
        return setting_dict

    def _update_tokens_from_swap_format(
        self, original_format, original_format_order, remove_obsolete=True
    ):
        """ Updates tokens based on a swap format call that will maintain synchronicity between token_dict and attrs
            If there was an accidental setting already set to one of the attrs that should now be a token attr due
            to the format swap, we wipe it and add a new TokenAttr to the Nomenclate attribute.

        :param original_format: str, original format string to compare to
        :param original_format_order: list(str), the original format order to compare to
        :param remove_obsolete: bool, whether to remove obsolete tokens
                                             if off: persistent state across format swaps of missing tokens
        """
        old_format_order = [_.lower() for _ in original_format_order]
        new_format_order = [_.lower() for _ in self.format_order]
        if hasattr(self, "token_dict") and self.format != original_format:
            old_tokens = [
                token
                for token in list(set(old_format_order) - set(new_format_order))
                if hasattr(self, token)
            ]

            new_tokens = [
                token
                for token in set(new_format_order) - set(old_format_order)
                if not hasattr(self, token) or isinstance(getattr(self, token, ""), str)
            ]

            self.merge_dict(dict.fromkeys(new_tokens, ""))

            if remove_obsolete:
                self.token_dict.purge_tokens(old_tokens)

                for new_token in new_tokens:
                    try:
                        delattr(self, new_token)
                    except AttributeError:
                        pass

    def _convert_input(self, *args, **kwargs):
        """ Takes variable inputs

        :param args: (dict, Nomenclate), any number of dictionary inputs or Nomenclates to be converted to dicts
        :param kwargs: str, any number of kwargs that represent token:value pairs
        :return: dict, combined dictionary of all inputs
        """
        args = [arg.state if isinstance(arg, Nomenclate) else arg for arg in args]
        input_dict = combine_dicts(*args, **kwargs)
        return input_dict

    def _sift_and_init_configs(self, input_dict):
        """ Removes all key/v for keys that exist in the overall config and activates them.
            Used to weed out config keys from tokens in a given input.
        """
        configs = {}
        for k, v in input_dict.items():
            if k not in map(str.lower, self.format_order) and any(
                [f_order.lower() in k for f_order in self.format_order]
            ):
                try:
                    self.CFG.get(self.CONFIG_ROOT + [k])
                except errors.ResourceNotFoundError:
                    pass
                finally:
                    configs[k] = v

        for key in configs.keys():
            input_dict.pop(key, None)
        if configs:
            self.initialize_overall_config_settings(input_dict=configs)

    def __eq__(self, other):
        return self.token_dict == other.token_dict

    def __str__(self):
        return self.get()

    def __setattr__(self, key, value):
        """ Custom setattr to detect whether they are trying to set a token, then updating the token_dict

        """
        if hasattr(self, "token_dict") and key in [s.lower() for s in self.format_order]:
            if getattr(self.token_dict, key):
                getattr(self.token_dict, key).set(value)
            else:
                self.token_dict.merge_serialization({key: value})
        else:
            object.__setattr__(self, key, value)

    def __getattr__(self, item):
        try:
            value = getattr(object.__getattribute__(self, "token_dict"), item)
        except AttributeError as error:
            try:
                value = object.__getattribute__(self, item)
            except AttributeError:
                raise error
        return value

    def __dir__(self):
        """ Taken from:
            http://techqa.info/programming/question/15507848/the-correct-way-to-override-the-__dir__-method-in-python

        """

        def get_attrs(obj):
            return obj.__dict__.keys()

        def dir_augment(obj):
            attrs = set()
            if not hasattr(obj, "__bases__"):
                # obj is an instance
                instance_class = obj.__class__
                attrs.update(get_attrs(instance_class))
                if hasattr(obj, "token_dict"):
                    attrs.update([token_attr.token for token_attr in obj.token_dict.token_attrs])
            else:
                # obj is a class
                instance_class = obj

            for cls in instance_class.__bases__:
                attrs.update(get_attrs(cls))
                attrs.update(dir_augment(cls))
            attrs.update(get_attrs(obj))
            return list(attrs)

        return dir_augment(self)

    def to_json(self):
        return {getattr(self, attr).to_json() for attr in self.SERIALIZE_ATTRS}

    def from_json(cls, json_blob):
        raise NotImplementedError

    def merge_json(self, json_blob):
        raise NotImplementedError
