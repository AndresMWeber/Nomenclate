import nomenclate.core.tokens as tokens
import nomenclate.core.errors as exceptions
from . import basetest


class TestTokenAttrBase(basetest.TestBase):
    def setUp(self):
        super(TestTokenAttrBase, self).setUp()
        self.token_attr = tokens.TokenAttr('test_label', 'test_token')
        self.fixtures.append(self.token_attr)


class TestTokenAttrInstantiate(TestTokenAttrBase):
    def test_empty_instantiate(self):
        self.assertEquals(tokens.TokenAttr().label, '')

    def test_valid_instantiate(self):
        self.fixtures.append(tokens.TokenAttr('test', 'test'))

    def test_invalid_instantiate_token_list(self):
        self.assertRaises(exceptions.ValidationError, tokens.TokenAttr, 'test', [])

    def test_invalid_instantiate_token_dict(self):
        self.assertRaises(exceptions.ValidationError, tokens.TokenAttr, 'test', {})

    def test_valid_instantiate_token(self):
        self.assertEquals(tokens.TokenAttr({}, 'test').label, "")

    def test_state(self):
        self.assertEquals(self.token_attr.label, 'test_label')
        self.assertEquals(self.token_attr.token, 'test_token')


class TestTokenAttrSet(TestTokenAttrBase):
    def test_set_invalid(self):
        with self.assertRaises(exceptions.ValidationError):
            tokens.TokenAttr().label = [1]
        with self.assertRaises(exceptions.ValidationError):
            tokens.TokenAttr().label = {1: 1}


class TestTokenAttrGet(TestTokenAttrBase):
    def test_get(self):
        self.assertEquals(self.token_attr.label, 'test_label')

    def test_get_empty(self):
        self.assertEquals(tokens.TokenAttr().label, '')