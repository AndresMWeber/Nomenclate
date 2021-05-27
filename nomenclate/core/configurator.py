import yaml
from typing import List
from collections import OrderedDict
from .tools import gen_dict_key_matches
from ..settings import TEMPLATE_YML_CONFIG_FILE_PATH, DEFAULT_YML_CONFIG_FILE
from .file_utils import (
    search_relative_cwd_user_dirs_for_file,
    validate_yaml_file,
    copy_file_to_home_dir,
)
from .errors import ResourceNotFoundError


class ConfigEntryFormatter(object):
    def format_query_result(self, query_result, query_path, return_type=list, preceding_depth=None):
        """ Formats the query result based on the return type requested.

        :param query_result: (dict or str or list), yaml query result
        :param query_path: (str, list(str)), representing query path
        :param return_type: type, return type of object user desires
        :param preceding_depth: int, the depth to which we want to encapsulate back up config tree
                                    -1 : defaults to entire tree
        :return: (dict, OrderedDict, str, list), specified return type
        """
        if type(query_result) != return_type:
            converted_result = self.format_with_handler(query_result, return_type)
        else:
            converted_result = query_result

        converted_result = self.add_preceding_dict(converted_result, query_path, preceding_depth)
        return converted_result

    def format_with_handler(self, query_result, return_type):
        """ Uses the callable handler to format the query result to the desired return type

        :param query_result: the result value of our query
        :param return_type: desired return type
        :return: type, the query value as the return type requested
        """
        handler = self.get_handler(type(query_result), return_type)
        return handler.format_result(query_result)

    @staticmethod
    def get_handler(query_result_type, return_type):
        """ Find the appropriate return type handler to convert the query result to the desired return type

        :param query_result_type: type, desired return type
        :param return_type: type, actual return type
        :return: callable, function that will handle the conversion
        """
        try:
            return FormatterRegistry.get_by_take_and_return_type(query_result_type, return_type)
        except (IndexError, AttributeError, KeyError):
            raise IndexError(
                "Could not find function in conversion list for input type %s and return type %s"
                % (query_result_type, return_type)
            )

    @staticmethod
    def add_preceding_dict(config_entry, query_path, preceding_depth):
        """ Adds the preceeding config keys to the config_entry to simulate the original full path to the config entry

        :param config_entry: object, the entry that was requested and returned from the config
        :param query_path: (str, list(str)), the original path to the config_entry
        :param preceding_depth: int, the depth to which we are recreating the preceding config keys
        :return: dict, simulated config to n * preceding_depth
        """
        if preceding_depth is None:
            return config_entry

        preceding_dict = {query_path[-1]: config_entry}
        path_length_minus_query_pos = len(query_path) - 1
        preceding_depth = (
            path_length_minus_query_pos - preceding_depth if preceding_depth != -1 else 0
        )

        for index in reversed(range(preceding_depth, path_length_minus_query_pos)):
            preceding_dict = {query_path[index]: preceding_dict}

        return preceding_dict


class ConfigParse(object):
    """ Responsible for finding + loading the configuration file contents then transmuting any config queries.
        It can also be simply set from a dictionary.
    """

    config_entry_handler = ConfigEntryFormatter()

    def __init__(self, data: dict = None, config_filename: str = None):
        """

        :param config_filepath: str, the path to a user specified config, or the nomenclate default
        """
        self.config = None
        self.config_filepath = None

        if data:
            self.set_from_dict(data)

        if config_filename:
            self.set_from_file(config_filename)

        if not self.config:
            self.create_user_config()

        self.function_type_lookup = {
            str: self._get_path_entry_from_string,
            list: self._get_path_entry_from_list,
        }

    def create_user_config(self):
        file_path = copy_file_to_home_dir(TEMPLATE_YML_CONFIG_FILE_PATH, DEFAULT_YML_CONFIG_FILE)
        self.set_from_file(file_path)

    def set_from_dict(self, data: dict):
        """ Set the config from a dictionary to allow for non-config file based real time modifications to the config.
        :param data: dict, the input data that will override the current config settings.
        """
        self.config = OrderedDict(sorted(data, key=lambda x: x[0], reverse=True))

    @classmethod
    def validate_config_file(cls, config_filename: str):
        return search_relative_cwd_user_dirs_for_file(config_filename, validator=validate_yaml_file)

    def set_from_file(self, config_filename):
        """ Loads from file and caches all data from the config file in the form of an OrderedDict to self.data

        :param config_filepath: str, the full filepath to the config file
        :return: bool, success status
        """
        self.config_filepath = self.validate_config_file(config_filename)
        config_data = None
        with open(self.config_filepath, "r") as f:
            config_data = yaml.safe_load(f)
        try:
            items = config_data.items()
        except AttributeError:
            items = list(config_data)
        finally:
            self.set_from_dict(items)

    def get(self, query_path=None, return_type=list, preceding_depth: int = None):
        """ Traverses the list of query paths to find the data requested

        :param query_path: (list(str), str), list of query path branches or query string
                                             Default behavior: returns list(str) of possible config headers
        :param return_type: (list, str, dict, OrderedDict), desired return type for the data
        :param preceding_depth: int, returns a dictionary containing the data that traces back up the path for x depth
                                     -1: for the full traversal back up the path
                                     None: is default for no traversal
        :return: (list, str, dict, OrderedDict), the type specified from return_type
        :raises: exceptions.ResourceNotFoundError: if the query path is invalid
        """
        if query_path is None:
            return self._default_config(return_type)

        try:
            config_entry = self.function_type_lookup.get(type(query_path), str)(query_path)
            query_result = self.config_entry_handler.format_query_result(
                config_entry, query_path, return_type=return_type, preceding_depth=preceding_depth
            )

            return query_result
        except IndexError:
            return return_type()

    def _get_path_entry_from_string(self, query_string, first_found=True, full_path=False):
        """ Parses a string to form a list of strings that represents a possible config entry header

        :param query_string: str, query string we are looking for
        :param first_found: bool, return first found entry or entire list
        :param full_path: bool, whether to return each entry with their corresponding config entry path
        :return: (Generator((list, str, dict, OrderedDict)), config entries that match the query string
        :raises: exceptions.ResourceNotFoundError
        """
        iter_matches = gen_dict_key_matches(query_string, self.config, full_path=full_path)
        try:
            return next(iter_matches) if first_found else iter_matches
        except (StopIteration, TypeError):
            raise ResourceNotFoundError(f"{query_string} not found in the config: {self.config}")

    def _get_path_entry_from_list(self, query_path):
        """ Returns the config entry at query path

        :param query_path: list(str), config header path to follow for entry
        :return: (list, str, dict, OrderedDict), config entry requested
        :raises: exceptions.ResourceNotFoundError
        """
        cur_data = self.config
        try:
            for child in query_path:
                cur_data = cur_data[child]
            return cur_data
        except (AttributeError, KeyError):
            raise ResourceNotFoundError("{query_path} not found in in the config.")

    def _default_config(self, return_type):
        """ Generates a default instance of whatever the type requested was (in case of miss)

        :param return_type: type, type of object requested
        :return: object, instance of return_type
        """
        if return_type == list:
            return [k for k in self.config]
        return return_type()


class FormatterRegistry(type):
    """ Factory class responsible for registering all input type to type conversions.
    E.G. - String -> List, Dict -> String etc.
    """

    CONVERSION_TABLE = {}

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)

        extensions = dct.get("converts")
        accepted_input_type = extensions.get("accepted_input_type", None)
        accepted_return_type = extensions.get("accepted_return_type", None)

        if accepted_input_type and accepted_return_type:
            take_exists = mcs.CONVERSION_TABLE.get(accepted_input_type)
            if not take_exists:
                mcs.CONVERSION_TABLE[accepted_input_type] = {}

            mcs.CONVERSION_TABLE[accepted_input_type][accepted_return_type] = cls

        return cls

    @classmethod
    def get_by_take_and_return_type(mcs, input_type, return_type):
        return mcs.CONVERSION_TABLE[input_type][return_type]


class BaseFormatter(metaclass=FormatterRegistry):
    converts = {"accepted_input_type": None, "accepted_return_type": None}

    @staticmethod
    def format_result(input):
        raise NotImplementedError


class StringToList(BaseFormatter):
    converts = {"accepted_input_type": str, "accepted_return_type": list}

    @staticmethod
    def format_result(input):
        return input.split()


class DictToString(BaseFormatter):
    converts = {"accepted_input_type": dict, "accepted_return_type": str}

    @staticmethod
    def format_result(input):
        return " ".join(list(input))


class DictToList(BaseFormatter):
    converts = {"accepted_input_type": dict, "accepted_return_type": list}

    @staticmethod
    def format_result(input):
        """ Always sorted for order
        """
        keys = list(input)
        keys.sort()
        return keys


class DictToOrderedDict(BaseFormatter):
    converts = {"accepted_input_type": dict, "accepted_return_type": OrderedDict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        items = list(input.items())
        return OrderedDict(sorted(items, key=lambda x: x[0]))


class OrderedDictToList(BaseFormatter):
    converts = {"accepted_input_type": OrderedDict, "accepted_return_type": list}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        return list(input)


class NoneToDict(BaseFormatter):
    converts = {"accepted_input_type": type(None), "accepted_return_type": dict}

    @staticmethod
    def format_result(input):
        """From: http://stackoverflow.com/questions/13062300/convert-a-dict-to-sorted-dict-in-python
        """
        return {}


class ListToString(BaseFormatter):
    converts = {"accepted_input_type": list, "accepted_return_type": str}

    @staticmethod
    def format_result(input):
        return " ".join(input)


class IntToList(BaseFormatter):
    converts = {"accepted_input_type": int, "accepted_return_type": list}

    @staticmethod
    def format_result(input):
        return [input]
