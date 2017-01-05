# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function

import unittest
import nomenclate.core.nomenclature as nm
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions


class TestBase(unittest.TestCase):
    def setUp(self):
        self.fixtures = []
        print ('running testBase setup!')

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    @staticmethod
    def checkEqual(L1, L2):
        return len(L1) == len(L2) and sorted(L1) == sorted(L2)


class TestTokenAttrBase(TestBase):
    def setUp(self):
        super(TestTokenAttrBase, self).setUp()
        self.token_attr = nm.TokenAttr('test_label', 'test_token')
        self.fixtures.append(self.token_attr)


class TestTokenAttrInstantiate(TestTokenAttrBase):
    def test_empty_instantiate(self):
        self.assertEquals(nm.TokenAttr().get(), '')

    def test_valid_instantiate(self):
        self.fixtures.append(nm.TokenAttr('test', 'test'))

    def test_invalid_instantiate_label(self):
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr, 'test', 1)

    def test_invalid_instantiate_token(self):
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr, 1, 'test')

    def test_state(self):
        self.assertEquals(self.token_attr.label, 'test_label')
        self.assertEquals(self.token_attr.token, 'test_token')


class TestTokenAttrSet(TestTokenAttrBase):
    def test_set_invalid(self):
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr().set, 1)
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr().set, [1])
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr().set, {1: 1})


class TestTokenAttrGet(TestTokenAttrBase):
    def test_get(self):
        self.assertEquals(self.token_attr.get(), 'test_label')

    def test_get_empty(self):
        self.assertEquals(nm.TokenAttr().get(), '')


class TestNomenclateBase(TestBase):
    def setUp(self):
        super(TestBase, self).setUp()
        self.cfg = config.ConfigParse()
        self.test_format = 'side_location_nameDecoratorVar_childtype_purpose_type'
        self.test_format_b = 'location_nameDecoratorVar_childtype_purpose_type_side'

        self.nom = nm.Nomenclate()

        # Inject our fake config
        self.nom.cfg = self.cfg
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.nom.var.set('A')
        self.fixtures =[self.cfg, self.nom, self.test_format_b, self.test_format]


class TestNomenclateTokens(TestNomenclateBase):
    pass


class TestNomenclateState(TestNomenclateBase):
    def test_state_clear(self):
        previous_state = self.nom.state
        self.nom.token_dict.clear_name_attrs()
        self.assertEquals(self.nom.state,
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.state = previous_state

    def test_state_purge(self):
        previous_state = self.nom.state
        self.nom.token_dict.purge_name_attrs()
        self.assertEquals(self.nom.state, {})
        self.nom.state = previous_state

    def test_state_valid(self):
        self.assertEquals(self.nom.state,
                          {'childtype': '',
                           'decorator': '',
                           'location': '',
                           'name': 'testObject',
                           'purpose': '',
                           'side': 'left',
                           'type': 'locator',
                           'var': 'A'})


class TestNomenclateResetFromConfig(TestNomenclateBase):
    def test_refresh(self):
       self.assertIsNone(self.nom.reset_from_config())


class TestNomenclateInitializeConfigSettings(TestNomenclateBase):
    pass


class TestNomenclateInitializeFormatOptions(TestNomenclateBase):
    def test_switch_naming_format_from_str(self):
        self.nom.initialize_format_options(self.test_format_b)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type']))

        self.nom.initialize_format_options(self.test_format)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type']))

    def test_switch_naming_format_from_config(self):
        self.nom.initialize_format_options(['naming_formats', 'node', 'format_lee'])
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['type', 'childtype', 'space', 'purpose', 'name', 'side']))
        self.nom.initialize_format_options(self.test_format)


class TestNomenclateInitializeOptions(TestNomenclateBase):
    def test_options_stored(self):
        self.nom.FORMATS_OPTIONS = None
        self.nom.CONFIG_OPTIONS = None
        self.nom.SUFFIX_OPTIONS = None
        self.nom.initialize_options()
        self.assertIsNotNone(self.nom.FORMATS_OPTIONS)
        self.assertIsNotNone(self.nom.SUFFIX_OPTIONS)
        self.assertIsNotNone(self.nom.CONFIG_OPTIONS)


class TestNomenclateInitializeUiOptions(TestNomenclateBase):
    def test_pass_through(self):
        self.nom.initialize_ui_options()


class TestNomenclateMergeDict(TestNomenclateBase):
    pass


class TestNomenclateGetFormatOrderFromFormatString(TestNomenclateBase):
    def test_get_format_order(self):
        self.assertEquals(self.nom.get_format_order_from_format_string(self.test_format),
                          ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type'])


class TestNomenclateGet(TestNomenclateBase):
    @unittest.skip("skipping until fixed")
    def test_get(self):
        self.assertEquals(self.nom.get(), 'left_testObject_LOC')

    @unittest.skip("skipping until fixed")
    def test_get_after_change(self):
        previous_state = self.nom.state
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'left_rear_testObject_LOC')
        self.nom.state = previous_state


class TestNomenclateGetChain(TestNomenclateBase):
    @unittest.skip("skipping until fixed")
    def test_get_chain(self):
        self.assertIsNone(self.nom.get_chain(0,5))


class TestNomenclateUpdateTokenAttributes(TestNomenclateBase):
    pass


class TestNomenclateComposeName(TestNomenclateBase):
    pass


class TestNomenclateValidateFormatString(TestNomenclateBase):
    def test_get__validate_format_string_valid(self):
        self.nom._validate_format_string('side_mide')

    def test_get__validate_format_string__is_format_invalid(self):
        self.assertRaises(exceptions.FormatError, self.nom._validate_format_string('notside'))


class TestNomenclateGetAlphanumericIndex(TestNomenclateBase):
    def test_get__get_alphanumeric_index_integer(self):
        self.assertEquals(self.nom._get_alphanumeric_index(0),
                          [0, 'int'])

    def test_get__get_alphanumeric_index_char_start(self):
        self.assertEquals(self.nom._get_alphanumeric_index('a'),
                          [0, 'char_lo'])

    def test_get__get_alphanumeric_index_char_end(self):
        self.assertEquals(self.nom._get_alphanumeric_index('z'),
                          [25, 'char_lo'])

    def test_get__get_alphanumeric_index_char_upper(self):
        self.assertEquals(self.nom._get_alphanumeric_index('B'),
                          [1, 'char_hi'])

    def test_get__get_alphanumeric_index_error(self):
        self.assertRaises(IOError, self.nom._get_alphanumeric_index, 'asdf')


class TestNomenclateCleanupFormattingString(TestNomenclateBase):
    def test_cleanup_format(self):
        print(self.nom.__dict__)
        self.assertEquals(self.nom.cleanup_formatted_string('test_name _messed __ up LOC'),
                          'test_name_messed_upLOC')


class TestNomenclateGetVariationId(TestNomenclateBase):
    def test_get_variation_id_normal(self):
        self.assertEquals(self.nom._get_variation_id(0), 'a')

    def test_get_variation_id_negative(self):
        self.assertEquals(self.nom._get_variation_id(-4), '')

    def test_get_variation_id_negative_one(self):
        self.assertEquals(self.nom._get_variation_id(-1), '')

    def test_get_variation_id_double_upper(self):
        self.assertEquals(self.nom._get_variation_id(1046, capital=True), 'ANG')

    def test_get_variation_id_double_lower(self):
        self.assertEquals(self.nom._get_variation_id(1046, capital=False), 'ang')


class TestNomenclateEq(TestNomenclateBase):
    def test_equal(self):
        print ('looking here')
        other = nm.Nomenclate(self.nom)
        print(self.nom.state, 'oh yeah')
        print(other.state, 'yeah')
        self.assertTrue(other == self.nom)

    def test_inequal_one_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        print(self.nom.state, 'oh yeah')
        print(other.state, 'yeah')
        self.assertFalse(other == self.nom)

    def test_inequal_multi_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        other.var = 'C'
        other.type = 'joint'
        print(self.nom.state, 'oh yeah')
        print(other.state, 'yeah')
        self.assertFalse(other == self.nom)


class TestNomenclateRepr(TestNomenclateBase):
    @unittest.skip("skipping until fixed")
    def test__repr__(self):
        self.assertEquals(self.nom.__repr__(), 'left_testObject_LOC')
