#!/usr/bin/env python
from . import errors as exceptions
import nomenclate.settings as settings
from . import tools


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

    SERIALIZE_ATTRS = ["token", "label", "case", "prefix", "suffix"]

    def __init__(self, token="", label=None, case="", prefix="", suffix=""):
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
        try:
            self.raw_string = int(label)
        except ValueError:
            self.raw_string = label

    def set(self, value):
        self.label = value

    @staticmethod
    def validate_entries(*entries):
        for entry in entries:
            if isinstance(entry, (str, int)) or entry is None:
                continue
            else:
                raise exceptions.ValidationError(
                    "Invalid type %s, expected %s" % (type(entry), str)
                )

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self_attrs = [getattr(self, attr) for attr in self.SERIALIZE_ATTRS]
            other_attrs = [getattr(other, attr) for attr in self.SERIALIZE_ATTRS]
            return self_attrs == other_attrs
        else:
            return False

    def __ne__(self, other):
        return (self.token, self.label) != (other.token, other.label)

    def __lt__(self, other):
        return (self.token, self.label) < (other.token, other.label)

    def __le__(self, other):
        return (self.token, self.label) <= (other.token, other.label)

    def __gt__(self, other):
        return (self.token, self.label) > (other.token, other.label)

    def __ge__(self, other):
        return (self.token, self.label) >= (other.token, other.label)

    def __str__(self):
        return "%r" % (self)

    def __repr__(self):
        return "<%s (%s): %r>" % (self.__class__.__name__, self.raw_token, self.to_json())

    def to_json(self):
        return {
            "token": self.raw_token,
            "label": self.raw_string,
            "case": self.case,
            "prefix": self.prefix,
            "suffix": self.suffix,
        }


class TokenAttrList(tools.Serializable):
    def __init__(self, token_attrs):
        self.token_attrs = [TokenAttr(token_attr, "") for token_attr in token_attrs]

    def reset(self):
        for token_attr in self.token_attrs:
            token_attr.set("")

    @property
    def unset_token_attrs(self):
        return [token_attr for token_attr in self.token_attrs if token_attr.label == ""]

    def purge_tokens(self, input_token_attrs=None):
        """ Removes all specified token_attrs that exist in instance.token_attrs
        
        :param token_attrs: list(str), list of string values of tokens to remove.  If None, removes all
        """
        if input_token_attrs is None:
            remove_attrs = self.token_attrs
        else:
            remove_attrs = [
                token_attr
                for token_attr in self.token_attrs
                if token_attr.token in input_token_attrs
            ]

        self.token_attrs = [
            token_attr for token_attr in self.token_attrs if token_attr not in remove_attrs
        ]

    @classmethod
    def from_json(cls, json_blob):
        instance = cls(list(json_blob))
        instance.merge_json(json_blob)
        return instance

    def merge_token_attr(self, token_attr):
        if self.has_token_attr(token_attr):
            getattr(self, token_attr.token).merge_json(token_attr.to_json())
        else:
            self.token_attrs.append(token_attr)

    def has_token_attr(self, token):
        return any([token_attr for token_attr in self.token_attrs if token_attr.token == token])

    def merge_json(self, json_blob):
        for token_name, token_attr_blob in json_blob.items():
            token_name = token_name.lower()
            try:
                if not isinstance(token_attr_blob, dict):
                    token_attr_blob = {"token": token_name, "label": token_attr_blob}

                getattr(self, token_name).merge_serialization(token_attr_blob)
            except (AttributeError, IndexError):
                self.merge_token_attr(TokenAttr.from_json(token_attr_blob))

    def to_json(self):
        return {token_attr.token: token_attr.to_json() for token_attr in self.token_attrs}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return all(
                map(
                    lambda x: x[0] == x[1],
                    zip(
                        sorted([t for t in self.token_attrs], key=lambda x: x.token),
                        sorted([t for t in other.token_attrs], key=lambda x: x.token),
                    ),
                )
            )
        return False

    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            try:
                return [token_attr for token_attr in self.token_attrs if token_attr.token == item][
                    0
                ]
            except IndexError:
                pass
        raise AttributeError

    def __str__(self):
        return " ".join(
            ["%s:%r" % (token_attr.token, token_attr.label) for token_attr in self.token_attrs]
        )

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.token_attrs)

    def __iter__(self):
        return iter(self.token_attrs)

    def __getitem__(self, item):
        return [token_attr for token_attr in self.token_attrs if token_attr.token == item][0]
