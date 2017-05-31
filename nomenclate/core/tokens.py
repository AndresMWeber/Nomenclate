#!/usr/bin/env python
from six import iteritems
from . import errors as exceptions
import nomenclate.settings as settings

MODULE_LEVEL_OVERRIDE = None


class TokenAttr(object):
    LOG = settings.get_module_logger(__name__, module_override_level=MODULE_LEVEL_OVERRIDE)

    def __init__(self, label=None, token=None):
        try:
            self.validate_entries(label)
        except exceptions.ValidationError:
            label = None
        self.validate_entries(token)
        self.raw_string = label if label is not None else ""
        self.raw_token = token
        self.case = None

    @property
    def token(self):
        return self.raw_token.lower()

    @token.setter
    def token(self, token):
        self.validate_entries(token)
        self.raw_token = token

    @property
    def label(self):
        string = None
        if self.case == 'upper':
            string = self.raw_string.upper()

        if self.case == 'lower':
            string = self.raw_string.lower()

        return string or self.raw_string

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
        if isinstance(other, type(self)):
            return self.token == other.token and self.label == other.label
        else:
            return False

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
            self.LOG.error(exceptions.SourceError('Instance has no %s token attribute set.' % token), exc_info=True)
        else:
            return token_attr

    def _create_token_attr(self, token, value):
        self.LOG.debug('_create_token_attr(%s:%s)' % (token, repr(value)))
        self.__dict__[token.lower()] = TokenAttr(label=value, token=token)

    def purge_tokens(self, token_attrs):
        """ Removes tokens not found in the format order
        """
        for token_attr in [_ for _ in token_attrs if _ in list(self.token_attrs)]:
            self.LOG.info('Deleting TokenAttr %s' % token_attr.token)
            delattr(self, token_attr.token)

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
            return all(map(lambda x: x[0] == x[1], zip(self.token_attrs, other.token_attrs)))
        return False

    def __getattr__(self, name):
        try:
            return self.__dict__[name]
        except KeyError:
            object.__getattribute__(self.__dict__, name)

    def __str__(self):
        return ' '.join(['%s:%s' % (token_attr.token, token_attr.label) for token_attr in self.token_attrs])
