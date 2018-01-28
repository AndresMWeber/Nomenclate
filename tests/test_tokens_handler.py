import nomenclate as nm
import nomenclate.core.tokens as tokens
from tests.basetest import TestBase


class TestTokenAttrBase(TestBase):
    def setUp(self):
        super(TestTokenAttrBase, self).setUp()
        self.nomenclate = nm.Nom()
        self.token_attr_dict_handler = tokens.TokenAttrList(self.nomenclate.token_dict.to_json())
        self.fixtures.append(self.token_attr_dict_handler)


class TestGetTokenAttr(TestTokenAttrBase):
    def test_get_existing(self):
        self.assertEquals(self.token_attr_dict_handler.name, tokens.TokenAttr('name', ''))

    def test_get_not_existing(self):
        self.assertRaises(AttributeError, getattr, self.token_attr_dict_handler, 'no')


class TestTokenAttrs(TestTokenAttrBase):
    def test_get(self):
        self.checkEqual(list(self.token_attr_dict_handler.token_attrs),
                        [tokens.TokenAttr('Var', ''),
                         tokens.TokenAttr('purpose', ''),
                         tokens.TokenAttr('type', ''),
                         tokens.TokenAttr('side', ''),
                         tokens.TokenAttr('location', ''),
                         tokens.TokenAttr('childtype', ''),
                         tokens.TokenAttr('name', ''),
                         tokens.TokenAttr('Decorator', '')])


class TestPurge(TestTokenAttrBase):
    def test_default(self):
        handler = tokens.TokenAttrList(self.nomenclate.state)
        handler.purge_tokens()
        self.assertEquals(handler.token_attrs, [])

    def test_input(self):
        handler = tokens.TokenAttrList(self.nomenclate.state)
        handler.purge_tokens([token.token for token in handler.token_attrs])
        self.assertEquals(handler.token_attrs, [])


class TestEq(TestTokenAttrBase):
    def test_not_equal(self):
        other_token_dict_handler = tokens.TokenAttrList(nm.Nom().token_dict.to_json())
        other_token_dict_handler.merge_json({'name': 'bob'})
        self.assertFalse(self.token_attr_dict_handler == other_token_dict_handler)

    def test_equal(self):
        self.assertTrue(self.token_attr_dict_handler == tokens.TokenAttrList(nm.Nom().token_dict.to_json()))

    def test_not_instance(self):
        self.assertFalse(self.token_attr_dict_handler == 5)


class TestStr(TestTokenAttrBase):
    def test_str(self):
        tokens = ['name', 'decorator', 'purpose', 'childtype', 'type', 'location', 'side', 'var']
        for token in tokens:
            self.assertIn(token, str(self.token_attr_dict_handler))
