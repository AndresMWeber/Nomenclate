#!/usr/bin/env python
from six import iteritems
from . import errors as exceptions
import nomenclate.settings as settings

MODULE_LEVEL_OVERRIDE = None


class TokenAttr(object):
    """ A TokenAttr represents a string token that we want to replace in a given nomenclate.core.formatter.FormatString
        It has 3 augmentation properties:

            TokenAttr().case
            TokenAttr().prefix
            TokenAttr().suffix

        These three settings enforce that after final rendering (finding matches in the config for the current
        token's label and any custom rendering syntax the user added) we will upper case the result and add
        either the given prefix or suffix no matter what.

    """
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LEVEL_OVERRIDE)

    def __init__(self, label=None, token=None):
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
        self.case_setting = ""
        self.prefix_setting = ""
        self.suffix_setting = ""

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

    @property
    def case(self):
        """ Get or set the current TokenAttr's case. Setting the case to either 'upper' or 'lower' means it will be validated and then
            added as the internal "raw_token" which will be used to look up any given config value or be used if
            no config value is found.

        """
        return self.case_setting

    @case.setter
    def case(self, case):
        if case in ['upper', 'lower']:
            self.case_setting = case

    @property
    def prefix(self):
        return self.prefix_setting

    @prefix.setter
    def prefix(self, prefix):
        if isinstance(prefix, str):
            self.prefix_setting = prefix

    @property
    def suffix(self):
        return self.suffix_setting

    @suffix.setter
    def suffix(self, suffix):
        if isinstance(suffix, str):
            self.suffix_setting = suffix

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
        if isinstance(other, type(self)):
            return self.token == other.token and self.label == other.label
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
        return str(self.label)

    def __repr__(self):
        return '<%s %s(%s):%r>' % (self.__class__.__name__, self.token, self.raw_token, self.label)



class TokenAttrDictHandler(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LEVEL_OVERRIDE)

    def __init__(self, nomenclate_object):
        self.nom = nomenclate_object
        self.LOG.info('Initializing TokenAttrDictHandler with default values %s' % self.empty_state)
        self.set_token_attrs(self.empty_state)

    @property
    def tokens(self):
        return [token.token for token in self.token_attrs]

    @property
    def token_attrs(self):
        return self.gen_object_token_attributes(self)

    @property
    def state(self):
        return dict((name_attr.token, name_attr.label) for name_attr in self.token_attrs)

    @state.setter
    def state(self, input_dict):
        self.set_token_attrs(input_dict)

    @property
    def empty_state(self):
        self.LOG.info("Generating empty initial state from format order: %s" % self.nom.format_order)
        return {token: "" for token in self.nom.format_order}

    @property
    def unset_token_attrs(self):
        return [token_attr for token_attr in self.token_attrs if token_attr.label == '']

    @property
    def token_attr_dict(self):
        return dict([(attr.token, attr.label) for attr in self.token_attrs])

    def reset(self):
        for token_attr in self.token_attrs:
            token_attr.set('')

    def set_token_attrs(self, input_dict):
        if not input_dict:
            self.LOG.info('No changes to make, ignoring...')
            return

        self.LOG.info('Setting token attributes %s against current state %s' % (input_dict, self.state))

        for input_attr_name, input_attr_value in iteritems(input_dict):
            self.set_token_attr(input_attr_name, input_attr_value)

        self.LOG.info('Finished setting attributes on TokenDict %s' % [attr for attr in list(self.token_attrs)])

    def set_token_attr(self, token, value):
        self.LOG.info('set_token_attr() - Setting TokenAttr %s with value %r' % (token, value))
        token_attrs = list(self.token_attrs)

        if token not in [token_attr.token for token_attr in token_attrs]:
            self.LOG.warning('Token did not exist, creating %r=%r...' % (token, value))
            self._create_token_attr(token, value)
        else:
            for token_attr in token_attrs:
                self.LOG.debug('Checking if token %r is equal to preexisting token %r' % (token, token_attr.token))
                if token == token_attr.token:
                    self.LOG.debug('Found matching token, setting value to %r' % value)
                    token_attr.label = value
                    break

        if hasattr(self.nom, 'token_dict'):
            token_attr_instance = getattr(self, token.lower())
            self.LOG.info('Passing token attr %r to the nomenclate object instance for updating' % token_attr_instance)
            self.nom.notifier.notify_observer(token.lower(), token_attr_instance)

    def get_token_attr(self, token):
        token_attr = getattr(self, token.lower())
        if token_attr is None:
            msg = 'Instance has no %s token attribute set.' % token
            self.LOG.warn(msg)
            raise exceptions.SourceError(msg)
        else:
            return token_attr

    def _create_token_attr(self, token, value):
        self.LOG.debug('_create_token_attr(%s:%s)' % (token, repr(value)))
        self.__dict__[token.lower()] = TokenAttr(label=value, token=token)

    def purge_tokens(self, token_attrs=None):
        """ Removes tokens not found in the format order
        """
        if token_attrs is None:
            token_attrs = self.tokens
        self.LOG.info('Starting purge for target tokens %s' % token_attrs)
        for token_attr in [_ for _ in token_attrs if _ in self.tokens]:
            self.LOG.info('Deleting TokenAttr %s' % token_attr)
            delattr(self, token_attr)

    @staticmethod
    def gen_object_token_attributes(obj):
        for name, value in iteritems(obj.__dict__):
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
            return all(map(lambda x: x[0] == x[1], zip(sorted(self.token_attrs, key=lambda x: x.token),
                                                       sorted(other.token_attrs, key=lambda x: x.token))))
        return False

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            object.__getattribute__(self.__dict__, name)

    def __str__(self):
        return ' '.join(['%s:%r' % (token_attr.token, token_attr.label) for token_attr in self.token_attrs])

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__,
                            ' '.join(['%s:%s' % (_.token, _.label) for _ in self.token_attrs]))
