#!/usr/bin/env python
import re
from . import errors as exceptions
import nomenclate.settings as settings



class FormatString(object):

    @property
    def format_order(self):
        return self.processed_format_order

    @format_order.setter
    def format_order(self, format_target):
        if format_target:
            self.processed_format_order = self.get_valid_format_order(format_target)
        else:
            self.processed_format_order = []

    def __init__(self, format_string=""):
        self.processed_format_order = []
        self.format_string = format_string
        self.format_order = self.format_string
        self.swap_format(format_string)

    def swap_format(self, format_target):
        try:
            self.format_order = format_target
            self.format_string = format_target
        except exceptions.FormatError as e:
            raise e

    @classmethod
    def parse_format_order(cls, format_target):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
            http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters

        :param format_target: str, format string we want to swap to
        :return: list(str), list of the matching tokens
        """
        try:
            pattern = re.compile(settings.FORMAT_STRING_REGEX)
            return [match.group() for match in pattern.finditer(format_target)]# if None not in match.groups()]
        except TypeError:
            raise exceptions.FormatError('Format string %s is not a valid input type, must be <type str>' %
                                         format_target)

    @classmethod
    def get_valid_format_order(cls, format_target, format_order=None):
        """ Checks to see if the target format string follows the proper style
        """
        format_order = format_order or cls.parse_format_order(format_target)
        cls.validate_no_token_duplicates(format_order)
        format_target = cls.remove_tokens(format_target, format_order)
        format_target = cls.remove_static_text(format_target)
        cls.validate_separator_characters(format_target)
        cls.validate_matched_parenthesis(format_target)
        return format_order

    @staticmethod
    def remove_tokens(format_target, format_order):
        for format_str in format_order:
            format_target = re.sub(format_str, '', format_target, count=1)
        return format_target

    @staticmethod
    def remove_static_text(format_target):
        return re.sub(settings.REGEX_STATIC_TOKEN, '', format_target)

    @classmethod
    def validate_separator_characters(cls, separator_characters):
        for char in separator_characters:
            if char not in settings.SEPARATORS:
                msg = "You have specified an invalid format string %s, must be separated by %s." % (
                    separator_characters,
                    settings.SEPARATORS)
                raise exceptions.FormatError(msg)

    @classmethod
    def validate_no_token_duplicates(cls, format_order):
        if len(format_order) != len(list(set([order.lower() for order in format_order]))):
            raise exceptions.FormatError("Format string has duplicate token names (capitalization insensitive).")

    @classmethod
    def validate_matched_parenthesis(cls, format_target):
        """ Adapted from https://stackoverflow.com/questions/6701853/parentheses-pairing-issue

        :param format_order:
        :return:
        """
        iparens = iter('(){}[]<>')
        parens = dict(zip(iparens, iparens))
        closing = parens.values()

        def balanced(astr):
            stack = []
            for c in astr:
                d = parens.get(c, None)
                if d:
                    stack.append(d)
                elif c in closing:
                    if not stack or c != stack.pop():
                        return False
            return not stack

        if format_target:
            if not balanced(format_target):
                raise exceptions.BalanceError("Format string has unmatching parentheses.")

    def __str__(self):
        return str(self.format_string)
