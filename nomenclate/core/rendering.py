#!/usr/bin/env python
from collections import Counter
import re
import string
import nomenclate.settings as settings
from . import processing


class InputRenderer(type):
    RENDER_FUNCTIONS = {}

    def __new__(mcs, name, bases, dct):
        cls = type.__new__(mcs, name, bases, dct)
        token = dct.get("token", None)
        if token:
            mcs.RENDER_FUNCTIONS[token] = cls
        return cls

    @classmethod
    def render_unique_tokens(cls, nomenclate_object, token_values):
        for token, token_settings in token_values.items():
            if token_settings.get("label") is not None and hasattr(nomenclate_object, token):
                value = token_settings.pop("label")
                token_settings.pop("token")

                renderer = cls.get_valid_render_function(token)
                if callable(getattr(renderer, "render")):
                    token_config = nomenclate_object.get_token_settings(token)
                    rendered_token = renderer.render(
                        value, token, nomenclate_object, **token_config
                    )
                    token_settings["label"] = rendered_token

    @classmethod
    def get_valid_render_function(cls, token_name):
        token_name = token_name.lower()
        renderer = None

        for func in list(cls.RENDER_FUNCTIONS):
            if token_name.replace(func, "").isdigit() or not token_name.replace(func, ""):
                renderer = func

        return cls.RENDER_FUNCTIONS.get(renderer or "default")

    @classmethod
    def render_nomenclative(cls, nomenclate_object):
        nomenclative = processing.Nomenclative(nomenclate_object.format)
        token_values = nomenclate_object.token_dict.to_json()
        cls.render_unique_tokens(nomenclate_object, token_values)
        render_template = nomenclate_object.format
        cls._prepend_token_match_objects(token_values, render_template)
        for token, match in token_values.items():
            nomenclative.add_match(*match)

        render_template = cls.cleanup_formatted_string(nomenclative.process_matches())
        return render_template

    @classmethod
    def _prepend_token_match_objects(cls, token_values, incomplete_nomenclative):
        for token, token_settings in token_values.items():
            value = token_settings["label"]
            regex_token = token.replace("(", "\(").replace(")", "\)")
            re_token = settings.REGEX_TOKEN_SEARCH.format(
                TOKEN=regex_token, TOKEN_CAPITALIZED=regex_token.capitalize()
            )
            re_matches = re.finditer(re_token, incomplete_nomenclative, 0)

            for re_match in re_matches:
                token_values[token] = (re_match, value)

        cls._clear_non_matches(token_values)

    @staticmethod
    def _clear_non_matches(token_values):
        to_delete = []
        for token, value in token_values.items():
            if isinstance(value, str) or not isinstance(value, tuple):
                to_delete.append(token)

        for delete in to_delete:
            token_values.pop(delete)

    @classmethod
    def cleanup_formatted_string(cls, formatted_string):
        """ Removes unused tokens/removes surrounding and double underscores

        :param formatted_string: str, string that has had tokens replaced
        :return: str, cleaned up name of object
        """
        # Remove whitespace
        result = formatted_string.replace(" ", "")
        # Remove any static token parentheses
        result = re.sub(settings.REGEX_PARENTHESIS, "", result)
        # Remove any multiple separator characters
        multi_character_matches = re.finditer("[%s]{2,}" % settings.SEPARATORS, result)
        for multi_character_match in sorted(
            multi_character_matches, key=lambda x: len(x.group()), reverse=True
        ):
            match = multi_character_match.group()
            most_common_separator = Counter(list(multi_character_match.group())).most_common(1)[0][
                0
            ]
            result = result.replace(match, most_common_separator)
        # Remove trailing or preceding non letter characters
        result = re.sub(settings.REGEX_ADJACENT_UNDERSCORE, "", result)
        #  not sure what this one was...but certainly not it.
        result = re.sub(settings.REGEX_SINGLE_PARENTHESIS, "", result)
        return result

    @staticmethod
    def _get_alphanumeric_index(query_string):
        """ Given an input string of either int or char, returns what index in the alphabet and case it is

        :param query_string: str, query string
        :return: (int, str), list of the index and type
        """
        # TODO: could probably rework this. it works, but it's ugly as hell.
        try:
            return [int(query_string), "int"]
        except ValueError:
            if len(query_string) == 1:
                if query_string.isupper():
                    return [string.ascii_uppercase.index(query_string), "char_hi"]
                elif query_string.islower():
                    return [string.ascii_lowercase.index(query_string), "char_lo"]
            else:
                raise IOError("The input is a string longer than one character")
