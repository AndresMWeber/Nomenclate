# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import unittest
from pyfakefs import fake_filesystem
import nomenclate.core.nomenclature as nm
import nomenclate.core.configurator as config


class TestNomenclate(unittest.TestCase):
    def setUp(self):
        self.cfg = config.ConfigParse()
        self.test_format = '{side}_{location}_{name}{decorator}J{var}_{childtype}_{purpose}_{type}'
        self.test_format_b = '{location}_{name}{decorator}J{var}_{childtype}_{purpose}_{type}_{side}'

        self.nom = nm.Nomenclate()

        # Inject our fake config
        self.nom.cfg = self.cfg
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.fixtures =[self.cfg, self.nom]

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    def test_refresh(self):
       self.assertIsNone(self.nom.refresh())

    def test_init_from_suffix_lut(self):
        self.assertIsNone(self.nom.init_from_suffix_lut())

    def test_get(self):
        self.assertEquals(self.nom.get(), 'left_testObject_LOC')

    def test_get_after_change(self):
        previous_state=self.nom.get_dict()
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'left_rear_testObject_LOC')
        self.nom.reset(previous_state)

    def test_get_dict_empty(self):
        previous_state=self.nom.get_dict()
        self.nom.reset({})
        self.assertEquals(self.nom.get_dict(),
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.reset(previous_state)

    def test_get_dict_non_empty(self):
        self.assertEquals(self.nom.get_dict(),
                          {'name': 'testObject', 'side': 'left', 'type': 'locator', 'decorator': '', 'location': '',
                           'var': '', 'purpose': '', 'childtype': ''})

    def test_get_chain(self):
        self.assertIsNone(self.nom.get_chain(0,5))

    def test_get_camel_case(self):
        self.assertEquals(self.nom.get_camel_case(self.test_format),
                          ['decorator', 'var'])

    def test_get_state_empty(self):
        self.assertIsNone(self.nom.get_state(input_dict={}))

    def test_get_state_valid(self):
        self.assertIsNone(self.nom.get_state(),
                          ['type:  #=', 'location:  #=',
                           'childType:  #=', 'side:  #=',
                           'decorator:  #=', 'var:  #=',
                           'purpose:  #=', 'name:  #='])

    def test_get_state_incomplete(self):
        self.assertIsNone(self.nom.get_state())

    def test_get_state_invalid(self):
        self.assertIsNone(self.nom.get_state())

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

    def test_get__is_format_valid(self):
        self.assertTrue(self.nom._is_format('side'))

    def test_get__is_format_invalid(self):
        self.assertFalse(self.nom._is_format('notside'))

    def test_get_format_order(self):
        self.assertEquals(self.nom.get_format_order(self.test_format),
                          ['side', 'location', 'name', 'decorator', 'var', 'childtype', 'purpose', 'type'])

    def test_cleanup_format(self):
        self.assertEquals(self.nom.cleanup_formatted_string('test_name _messed __ up LOC'),
                          'test_name_messed_upLOC')

    def test_switch_naming_format(self):
        self.assertTrue(self.nom.initialize_format_options(self.test_format_b))

        self.assertTrue(self.nom.initialize_format_options(self.test_format))

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

    def test__repr__(self):
        self.assertEquals(self.nom.__repr__(), 'left_testObject_LOC')