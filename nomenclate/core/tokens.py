#!/usr/bin/env python
from six import iteritems
from . import errors as exceptions
import nomenclate.settings as settings
from . import tools

MODULE_LEVEL_OVERRIDE = settings.INFO


class TokenAttr(tools.Serializable):
    """ A TokenAttr represents a string token that we want to replace in a given nomenclate.core.formatter.FormatString
        It has 3 augmentation properties:

            TokenAttr().case
            TokenAttr().prefix
            TokenAttr().suffix

        These three settings enforce that after final rendering (finding matches in the config for the current
        token's label and any custom rendering syntax the user added) we will upper case the result and add
        either the given prefix or suffix no matter what.

    """
    SERIALIZE_ATTRS = ['token', 'label', 'case', 'prefix', 'suffix']

    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LEVEL_OVERRIDE)

    def __init__(self, label=None, token='', case='', prefix='', suffix=''):
        """

        :param label: str, the label is represents the value we want to replace the given token with
        :param token: str, the raw name for the token to be used
        """
        try:
            self.validate_entries(label)
        except exceptions.ValidationError:
            label = None
        self.validate_entries(token)

        self.raw_string = label if label is not None else ""
        self.raw_token = token
        self.case = case
        self.prefix = prefix
        self.suffix = suffix

    @property
    def token(self):
        """ Get or set the current token. Setting the token to a new value means it will be validated and then
            added as the internal "raw_token" which will be used to look up any given config value or be used if
            no config value is found.

        """
        return self.raw_token.lower()

    @token.setter
    def token(self, token):
        self.validate_entries(token)
        self.raw_token = token

    @property
    def label(self):
        """ Get or set the current token's "label" or value. Setting the label to a new value means it will be added
            as the internal "raw_string" which will be used to look up any given config value or be used if no config
            value is found.

        """
        return self.raw_string

    @label.setter
    def label(self, label):
        self.validate_entries(label)
        self.LOG.debug('Setting token attr %s -> %r' % (str(self), label))
        self.raw_string = label
        self.LOG.debug('%r and the raw_string is %s' % (self, self.raw_string))

    def set(self, value):
        self.label = value

    @staticmethod
    def validate_entries(*entries):
        for entry in entries:
            if isinstance(entry, (str, int)) or entry is None:
                continue
            else:
                raise exceptions.ValidationError('Invalid type %s, expected %s' % (type(entry), str))

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self_attrs = [getattr(self, attr) for attr in self.SERIALIZE_ATTRS]
            other_attrs = [getattr(other, attr) for attr in self.SERIALIZE_ATTRS]
            return self_attrs == other_attrs
        else:
            return False

    def __ne__(self, other):
        return ((self.token, self.label) != (other.token, other.label))

    def __lt__(self, other):
        return ((self.token, self.label) < (other.token, other.label))

    def __le__(self, other):
        return ((self.token, self.label) <= (other.token, other.label))

    def __gt__(self, other):
        return ((self.token, self.label) > (other.token, other.label))

    def __ge__(self, other):
        return ((self.token, self.label) >= (other.token, other.label))

    def __str__(self):
        return '%r' % (self)

    def __repr__(self):
        return '<%s (%s): %r>' % (self.__class__.__name__, self.raw_token, self.to_json())

    def to_json(self):
        return {"token": self.raw_token,
                "label": self.raw_string,
                "case": self.case,
                "prefix": self.prefix,
                "suffix": self.suffix,
                }


class TokenAttrDictHandler(tools.Serializable):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LEVEL_OVERRIDE)

    def __init__(self, token_attrs):
        self.token_attrs = {token_attr.lower(): TokenAttr('', token_attr) for token_attr in token_attrs}

    def reset(self):
        for _, token_attr in iteritems(self.token_attrs):
            token_attr.set('')

    def purge_tokens(self, token_attrs=None):
        """ Removes all specified token_attrs that exist in instance.token_attrs
        
        :param token_attrs: list(str), list of string values of tokens to remove.  If None, removes all
        """
        if token_attrs is None:
            token_attrs = list(self.token_attrs)
        else:
            token_attrs = [token_attr.token for _, token_attr in iteritems(self.token_attrs) if
                           token_attr.token in token_attrs]

        self.LOG.info('Starting purge for target tokens %s' % token_attrs)

        for token_attr in token_attrs:
            self.LOG.info('Deleting TokenAttr %s' % token_attr)
            delattr(self, token_attr)

    @classmethod
    def from_json(cls, json_blob):
        instance = cls(list(json_blob))
        instance.merge_json(json_blob)
        return instance

    def merge_json(self, json_blob):
        self.LOG.info('Merging token attributes %s against current tokens: %s' % (json_blob, self.token_attrs))
        for token_name, token_attr_blob in iteritems(json_blob):
            token_name = token_name.lower()
            try:
                if not isinstance(token_attr_blob, dict):
                    token_attr_blob = {'token': token_name, 'label': token_attr_blob}
                    self.LOG.info('Detected single string input for token %s, treating as label input.' % token_name)
                self.LOG.info('Attempting to merge TokenAttr: %s with blob %s' % (token_name, token_attr_blob))
                self.token_attrs[token_name].merge_serialization(token_attr_blob)
            except KeyError:
                self.LOG.info('Token %s did not exist, added and set with input %s' % (token_name, token_attr_blob))
                setattr(self, token_name, TokenAttr.from_json(token_attr_blob))
        self.LOG.info('Finished setting attributes on TokenDict %s' % [attr for attr in list(self.token_attrs)])

    def to_json(self):
        return {token.lower(): token_attr.to_json() for token, token_attr in iteritems(self.token_attrs)}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(map(lambda x: x[0] == x[1],
                           zip(sorted([t for _, t in iteritems(self.token_attrs)], key=lambda x: x.token),
                               sorted([t for _, t in iteritems(other.token_attrs)], key=lambda x: x.token))))
        return False

    def __getattr__(self, name):
        try:
            value = object.__getattribute__(self, name)
        except AttributeError:
            try:
                value = self.token_attrs[name]
            except KeyError:
                raise AttributeError
        return value

    def __delattr__(self, item):
        try:
            object.__delattr__(self, item)
        except AttributeError:
            try:
                self.token_attrs.pop(item)
            except KeyError:
                raise AttributeError

    def __str__(self):
        return ' '.join(
            ['%s:%r' % (token_attr.token, token_attr.label) for _, token_attr in iteritems(self.token_attrs)])

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            ' '.join(['%s:%s' % (token_attr.token, token_attr.label) for _, token_attr in
                                      iteritems(self.token_attrs)]))

    def __iter__(self):
        return iteritems(self.token_attrs)

    def __getitem__(self, item):
        return self.token_attrs.get(item)
