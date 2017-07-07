#!/usr/bin/env python
import re
from . import errors as exceptions
import nomenclate.settings as settings

MODULE_LOGGER_LEVEL_OVERRIDE = settings.DEBUG


class FormatString(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LOGGER_LEVEL_OVERRIDE)

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
        self.LOG.info('Initializing format string with input %r' % format_string)
        self.processed_format_order = []
        self.format_string = format_string
        self.format_order = self.format_string
        self.swap_format(format_string)

    def swap_format(self, format_target):
        try:
            self.format_order = format_target
            self.format_string = format_target
            self.LOG.debug('Successfully set format string: %s and format order: %s' % (self.format_string,
                                                                                        self.format_order))
        except exceptions.FormatError as e:
            msg = "Could not validate input format target %s" % format_target
            self.LOG.error(msg)
            raise e

    def parse_format_order(self, format_target):
        """ Dissects the format string and gets the order of the tokens as it finds them l->r
            Splits on camel case or periods/underscores
            Modified version from this:
            http://stackoverflow.com/questions/2277352/python-split-a-string-at-uppercase-letters

        :param format_target: str, format string we want to swap to
        :return: list(str), list of the matching tokens
        """
        self.LOG.debug('Getting format order from target %s' % repr(format_target))
        try:
            pattern = re.compile(settings.FORMAT_STRING_REGEX)
            return [match.group() for match in pattern.finditer(format_target)]# if None not in match.groups()]
        except TypeError:
            raise exceptions.FormatError('Format string %s is not a valid input type, must be <type str>' %
                                         format_target)

    def get_valid_format_order(self, format_target, format_order=None):
        """ Checks to see if the target format string follows the proper style
        """
        self.LOG.debug('Validating format target %r and parsing for format order %r.' % (format_target, format_order))
        format_order = format_order or self.parse_format_order(format_target)
        self.LOG.debug('Resulting format order is %s' % format_order)
        self.validate_no_token_duplicates(format_order)
        format_target = self.remove_tokens(format_target, format_order)
        format_target = self.remove_static_text(format_target)
        self.validate_separator_characters(format_target)
        self.LOG.debug('After processing format_target is (should only be valid separator chars): %s' % format_target)
        return format_order

    def remove_tokens(self, format_target, format_order):
        for format_str in format_order:
            format_target = re.sub(format_str, '', format_target, count=1)
        return format_target

    def remove_static_text(self, format_target):
        return re.sub(settings.REGEX_STATIC_TOKEN, '', format_target)

    def validate_separator_characters(self, separator_characters):
        self.LOG.debug('Validating leftover separator characters %s' % separator_characters)
        for char in separator_characters:
            if char not in settings.SEPARATORS:
                msg = "You have specified an invalid format string %s, must be separated by %s." % (
                    separator_characters,
                    settings.SEPARATORS)
                self.LOG.warning(msg)
                raise exceptions.FormatError(msg)

    def validate_no_token_duplicates(self, format_order):
        if len(format_order) != len(list(set([order.lower() for order in format_order]))):
            msg = "Format string has duplicate token names (capitalization insensitive).  Please correct."
            self.LOG.warning(msg)
            raise exceptions.FormatError(msg)

    def __str__(self):
        return str(self.format_string)
