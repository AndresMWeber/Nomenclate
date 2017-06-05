import nomenclate
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


class TestTokenStr(TestTokenAttrBase):
    def test_label_valid(self):
        token_attr = tokens.TokenAttr('bob', 'name')
        self.assertEquals(str(token_attr), 'bob')

    def test_label_empty(self):
        token_attr = tokens.TokenAttr('', 'name')
        self.assertEquals(str(token_attr), '')


class TestTokenRepr(TestTokenAttrBase):
    @staticmethod
    def build_repr(token_attr):
        return '<%s %s(%s):%r>' % (token_attr.__class__.__name__,
                                   token_attr.token,
                                   token_attr.raw_token,
                                   token_attr.label)

    def test_label_valid(self):
        token_attr = tokens.TokenAttr('bob', 'name')
        self.assertEquals(repr(token_attr), self.build_repr(token_attr))

    def test_label_empty(self):
        token_attr = tokens.TokenAttr('', 'name')
        self.assertEquals(repr(token_attr), self.build_repr(token_attr))


class TestTokenToken(TestTokenAttrBase):
    def test_token_valid(self):
        token_attr = tokens.TokenAttr('bob', 'name')
        self.assertEquals(token_attr.token, 'name')

    def test_token_empty(self):
        token_attr = tokens.TokenAttr('bob', '')
        self.assertEquals(token_attr.token, '')

    def test_token_set(self):
        token_attr = tokens.TokenAttr('bob', '')
        self.assertEquals(token_attr.token, '')
        token_attr.token = 'name'
        self.assertEquals(token_attr.token, 'name')


class TestTokenLabel(TestTokenAttrBase):
    def test_normal_get(self):
        token_attr = tokens.TokenAttr('Bob', 'name')
        self.assertEquals(token_attr.label, 'Bob')


class TestTokenEq(TestTokenAttrBase):
    def test_equal(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') == tokens.TokenAttr('Bob', 'name'))

    def test_not_equal_label(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') == tokens.TokenAttr('Fob', 'name'))

    def test_not_equal_token(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') == tokens.TokenAttr('Bob', 'fame'))

    def test_non_token(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') == '<TokenAttr name(name):\'Bob\'>')

class TestTokenNe(TestTokenAttrBase):
    def test_equal(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') != tokens.TokenAttr('Bob', 'name'))

    def test_not_equal_label(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') != tokens.TokenAttr('Fob', 'name'))

    def test_not_equal_token(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') != tokens.TokenAttr('Bob', 'fame'))

    def test_non_token(self):
        self.assertRaises(AttributeError, tokens.TokenAttr('Bob', 'name').__ne__, '<TokenAttr name(name):\'Bob\'>')

class TestTokenLe(TestTokenAttrBase):
    def test_equal(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Bob', 'name'))

    def test_not_equal_label(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Fob', 'name'))

    def test_not_equal_token(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Bob', 'fame'))

    def test_non_token(self):
        self.assertRaises(AttributeError, tokens.TokenAttr('Bob', 'name').__le__, '<TokenAttr name(name):\'Bob\'>')


class TestTokenGe(TestTokenAttrBase):
    def test_equal(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Bob', 'name'))

    def test_not_equal_label(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Fob', 'name'))

    def test_not_equal_token(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') >= tokens.TokenAttr('Bob', 'fame'))

    def test_non_token(self):
        self.assertRaises(AttributeError, tokens.TokenAttr('Bob', 'name').__ge__, '<TokenAttr name(name):\'Bob\'>')


class TestTokenGt(TestTokenAttrBase):
    def test_equal(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') > tokens.TokenAttr('Bob', 'name'))

    def test_not_equal_label(self):
        self.assertFalse(tokens.TokenAttr('Bob', 'name') > tokens.TokenAttr('Fob', 'name'))

    def test_not_equal_token(self):
        self.assertTrue(tokens.TokenAttr('Bob', 'name') > tokens.TokenAttr('Bob', 'fame'))

    def test_non_token(self):
        self.assertRaises(AttributeError, tokens.TokenAttr('Bob', 'name').__gt__, '<TokenAttr name(name):\'Bob\'>')