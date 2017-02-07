# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
import unittest
import re
from pprint import pprint
import nomenclate.core.nomenclature as nm
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions


class TestBase(unittest.TestCase):
    def setUp(self):
        self.fixtures = []
        print('running testBase setup!')

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
        self.assertEquals(nm.TokenAttr().label, '')

    def test_valid_instantiate(self):
        self.fixtures.append(nm.TokenAttr('test', 'test'))

    def test_invalid_instantiate_label(self):
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr, 'test', [])

    def test_invalid_instantiate_token(self):
        self.assertRaises(exceptions.ValidationError, nm.TokenAttr, {}, 'test')

    def test_state(self):
        self.assertEquals(self.token_attr.label, 'test_label')
        self.assertEquals(self.token_attr.token, 'test_token')


class TestTokenAttrSet(TestTokenAttrBase):
    def test_set_invalid(self):
        with self.assertRaises(exceptions.ValidationError):
            nm.TokenAttr().label = [1]
        with self.assertRaises(exceptions.ValidationError):
            nm.TokenAttr().label = {1: 1}


class TestTokenAttrGet(TestTokenAttrBase):
    def test_get(self):
        self.assertEquals(self.token_attr.label, 'test_label')

    def test_get_empty(self):
        self.assertEquals(nm.TokenAttr().label, '')


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
        self.fixtures = [self.cfg, self.nom, self.test_format_b, self.test_format]


class TestNomenclateTokens(TestNomenclateBase):
    pass


class TestNomenclateState(TestNomenclateBase):
    def test_state_clear(self):
        previous_state = self.nom.state
        self.nom.token_dict.reset()
        self.assertEquals(self.nom.state,
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.state = previous_state

    @unittest.skip
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
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

        self.nom.initialize_format_options(self.test_format)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

    def test_switch_naming_format_from_config(self):
        self.nom.initialize_format_options(['naming_formats', 'node', 'format_lee'])
        print(self.nom.format_order)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['type', 'childtype', 'space', 'purpose', 'name', 'side']))
        self.nom.initialize_format_options(self.test_format)


class TestNomenclateInitializeOptions(TestNomenclateBase):
    def test_options_stored(self):
        self.nom.CONFIG_OPTIONS = None
        self.nom.initialize_options()
        self.assertIsNotNone(self.nom.CONFIG_OPTIONS)


class TestNomenclateInitializeUiOptions(TestNomenclateBase):
    def test_pass_through(self):
        self.nom.initialize_ui_options()


class TestNomenclateMergeDict(TestNomenclateBase):
    pass


class TestNomenclateGetFormatOrderFromFormatString(TestNomenclateBase):
    def test_get_format_order(self):
        self.assertEquals(self.nom.format_string_object.parse_format_order(self.test_format),
                          ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type'])


class TestNomenclateGet(TestNomenclateBase):
    def test_get(self):
        print(self.nom.state)
        self.assertEquals(self.nom.get(), 'l_testObjectA_LOC')

    def test_get_after_change(self):
        previous_state = self.nom.state
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'l_rr_testObjectA_LOC')
        self.nom.state = previous_state


class TestNomenclateGetChain(TestNomenclateBase):
    def test_get_chain(self):
        self.assertIsNone(self.nom.get_chain(0, 5))


class TestNomenclateUpdateTokenAttributes(TestNomenclateBase):
    pass


class TestNomenclateComposeName(TestNomenclateBase):
    pass


class TestNomenclateEq(TestNomenclateBase):
    def test_equal(self):
        other = nm.Nomenclate(self.nom)
        self.assertTrue(other == self.nom)

    def test_inequal_one_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        self.assertFalse(other == self.nom)

    def test_inequal_multi_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        other.var = 'C'
        other.type = 'joint'
        self.assertFalse(other == self.nom)


class TestNomenclateRepr(TestNomenclateBase):
    def test__str__(self):
        self.assertEquals(str(self.nom), 'l_testObjectA_LOC')


class TestFormatStringBase(TestBase):
    def setUp(self):
        super(TestFormatStringBase, self).setUp()
        self.fs = nm.FormatString()
        self.fixtures.append(self.fs)


class TestFormatStringValidateFormatString(TestFormatStringBase):
    def test_get__validate_format_string_valid(self):
        self.fs.get_valid_format_order('side_mide')

    def test_get__validate_format_string__is_format_invalid(self):
        print(repr(self))
        self.assertRaises(exceptions.FormatError, self.fs.get_valid_format_order, 'notside;blah')
