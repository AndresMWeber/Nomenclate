# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function

import unittest
import nomenclate.core.nomenclature as nm
import nomenclate.core.configurator as config
import nomenclate.core.exceptions as exceptions


class TestNomenclate(unittest.TestCase):
    def setUp(self):
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
        self.fixtures =[self.cfg, self.nom]

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    def test_refresh(self):
       self.assertIsNone(self.nom.reset_from_config())

    def test_init_from_suffix_lut(self):
        self.nom.initialize_options()

    @unittest.skip("skipping until fixed")
    def test_get(self):
        self.assertEquals(self.nom.get(), 'left_testObject_LOC')

    @unittest.skip("skipping until fixed")
    def test_get_after_change(self):
        previous_state = self.nom.state
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'left_rear_testObject_LOC')
        self.nom.state = previous_state

    @unittest.skip("skipping until fixed")
    def test_get_dict_empty(self):
        previous_state = self.nom.state
        self.nom.clear_name_attrs()
        self.assertEquals(self.nom.state,
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.state = previous_state

    @unittest.skip("skipping until fixed")
    def test_get_dict_non_empty(self):
        self.assertEquals(self.nom.state,
                          {'name': 'testObject', 'side': 'left', 'type': 'locator', 'decorator': '', 'location': '',
                           'var': '', 'purpose': '', 'childtype': ''})

    @unittest.skip("skipping until fixed")
    def test_get_chain(self):
        self.assertIsNone(self.nom.get_chain(0,5))

    def test_get_state_empty(self):
        previous_state = self.nom.state
        self.nom.token_dict.purge_name_attrs()
        self.assertEquals(self.nom.state, {})
        self.nom.state = previous_state

    @unittest.skip("skipping until fixed")
    def test_get_state_valid(self):
        self.assertEquals(self.nom.state,
                          {'type': '',
                           'location': '',
                           'childType': '',
                           'decorator': '',
                           'purpose': ''})

    def test_get__get_str_or_int_abc_pos_integer(self):
        self.assertEquals(self.nom._get_alphanumeric_index(0),
                          [0, 'int'])

    def test_get__get_str_or_int_abc_pos_char_start(self):
        self.assertEquals(self.nom._get_alphanumeric_index('a'),
                          [0, 'char_lo'])

    def test_get__get_str_or_int_abc_pos_char_end(self):
        self.assertEquals(self.nom._get_alphanumeric_index('z'),
                          [25, 'char_lo'])

    def test_get__get_str_or_int_abc_pos_char_upper(self):
        self.assertEquals(self.nom._get_alphanumeric_index('B'),
                          [1, 'char_hi'])

    def test_get__get_str_or_int_abc_pos_error(self):
        self.assertRaises(IOError, self.nom._get_alphanumeric_index, 'asdf')

    def test_get__validate_format_string_valid(self):
        self.nom._validate_format_string('side_mide')

    def test_get__validate_format_string__is_format_invalid(self):
        self.assertRaises(exceptions.FormatError, self.nom._validate_format_string('notside'))

    def test_get_format_order(self):
        self.assertEquals(self.nom.get_format_order_from_format_string(self.test_format),
                          ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type'])

    def test_cleanup_format(self):
        self.assertEquals(self.nom.cleanup_formatted_string('test_name _messed __ up LOC'),
                          'test_name_messed_upLOC')

    @unittest.skip("skipping until fixed")
    def test_switch_naming_format(self):
        self.assertTrue(self.nom.initialize_format_options(self.test_format_b))

        self.assertTrue(self.nom.initialize_format_options(self.test_format))

    @unittest.skip("skipping until fixed")
    def test_switch_naming_format_from_config(self):
        self.assertTrue(self.nom.initialize_format_options('format_b'))

        self.assertTrue(self.nom.initialize_format_options(self.test_format))

    def test_get_alpha_normal(self):
        self.assertEquals(self.nom.get_variation_id(0), 'a')

    def test_get_alpha_negative(self):
        self.assertEquals(self.nom.get_variation_id(-4), '')

    def test_get_alpha_negative_one(self):
        self.assertEquals(self.nom.get_variation_id(-1), '')

    def test_get_alpha_double_upper(self):
        self.assertEquals(self.nom.get_variation_id(1046, capital=True), 'ANG')

    def test_get_alpha_double_lower(self):
        self.assertEquals(self.nom.get_variation_id(1046, capital=False), 'ang')

    @unittest.skip("skipping until fixed")
    def test__repr__(self):
        self.assertEquals(self.nom.__repr__(), 'left_testObject_LOC')