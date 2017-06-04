import nomenclate as nm
import nomenclate.core.tokens as tokens
import nomenclate.core.errors as exceptions
from . import basetest


class TestTokenAttrBase(basetest.TestBase):
    def setUp(self):
        super(TestTokenAttrBase, self).setUp()
        self.nomenclate = nm.Nom()
        self.token_attr_dict_handler = tokens.TokenAttrDictHandler(self.nomenclate)
        self.fixtures.append(self.token_attr_dict_handler, )


class TestGetTokenAttr(TestTokenAttrBase):
    def test_get_existing(self):
        self.assertEquals(self.token_attr_dict_handler.get_token_attr('name'), tokens.TokenAttr('', 'name'))

    def test_get_not_existing(self):
        self.assertRaises(AttributeError, self.token_attr_dict_handler.get_token_attr, 'no')

    def test_is_none(self):
        token_attr = self.token_attr_dict_handler.get_token_attr('name')
        setattr(self.token_attr_dict_handler, token_attr.token, None)
        print(getattr(self.token_attr_dict_handler, token_attr.token))
        self.assertRaises(exceptions.SourceError, self.token_attr_dict_handler.get_token_attr, 'name')
        setattr(self.token_attr_dict_handler, token_attr.token, token_attr)


class TestTokenAttrs(TestTokenAttrBase):
    def test_get(self):
        self.checkEqual(list(self.token_attr_dict_handler.token_attrs),
                        [tokens.TokenAttr('', 'Var'),
                         tokens.TokenAttr('', 'purpose'),
                         tokens.TokenAttr('', 'type'),
                         tokens.TokenAttr('', 'side'),
                         tokens.TokenAttr('', 'location'),
                         tokens.TokenAttr('', 'childtype'),
                         tokens.TokenAttr('', 'name'),
                         tokens.TokenAttr('', 'Decorator')])


class TestPurge(TestTokenAttrBase):
    def test_default(self):
        handler = tokens.TokenAttrDictHandler(self.nomenclate)
        handler.purge_tokens()
        self.assertEquals(list(handler.token_attrs), [])

    def test_input(self):
        handler = tokens.TokenAttrDictHandler(self.nomenclate)
        handler.purge_tokens([token.token for token in handler.token_attrs])
        self.assertEquals(list(handler.token_attrs), [])


class TestValidateNameInFormatOrder(TestTokenAttrBase):
    def test_not_existing(self):
        handler = tokens.TokenAttrDictHandler(self.nomenclate)
        self.assertRaises(exceptions.FormatError,
                          handler._validate_name_in_format_order,
                          'no',
                          self.nomenclate.format_order)

    def test_existing(self):
        handler = tokens.TokenAttrDictHandler(self.nomenclate)
        handler._validate_name_in_format_order('name', self.nomenclate.format_order)


class TestEq(TestTokenAttrBase):
    def test_not_equal(self):
        other_token_dict_handler = tokens.TokenAttrDictHandler(nm.Nom())
        other_token_dict_handler.set_token_attrs({'name': 'bob'})
        self.assertFalse(self.token_attr_dict_handler == other_token_dict_handler)

    def test_equal(self):
        self.assertTrue(self.token_attr_dict_handler == tokens.TokenAttrDictHandler(nm.Nom()))

    def test_not_instance(self):
        self.assertFalse(self.token_attr_dict_handler == 5)


class TestStr(TestTokenAttrBase):
    def test_str(self):
        tokens = ['name', 'decorator', 'purpose', 'childtype', 'type', 'location', 'side', 'var']
        for token in tokens:
            self.assertIn(token, str(self.token_attr_dict_handler))
