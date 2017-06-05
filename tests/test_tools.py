from collections import OrderedDict
import nomenclate as nm
from . import basetest
from nomenclate.core.tools import (
    combine_dicts,
    gen_dict_key_matches,
    get_keys_containing
)


class TestCombineDicts(basetest.TestBase):
    def test_with_dict_with_nomenclate_object(self):
        self.assertDictEqual(combine_dicts({1: 1, 2: 2, 3: 3}, nm.Nom(name='test', purpose='lots').state),
                             {'decorator': '', 1: 1, 2: 2, 3: 3, 'name': 'test', 'type': '', 'side': '',
                              'childtype': '', 'var': '', 'location': '', 'purpose': 'lots'})

    def test_only_dicts(self):
        self.assertDictEqual(combine_dicts({1: 1, 2: 2, 3: 3}, {4: 4, 5: 5, 6: 6}),
                             {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6})

    def test_no_dicts_or_kwargs(self):
        self.assertDictEqual(combine_dicts('five', 5, None, [], 'haha'),
                             {})

    def test_kwargs(self):
        self.assertDictEqual(combine_dicts(parse='test', plush=5),
                             {'parse': 'test', 'plush': 5})

    def test_dicts_and_kwargs(self):
        self.assertDictEqual(combine_dicts({1: 1, 2: 2, 3: 3}, {4: 4, 5: 5, 6: 6}, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6})

    def test_dicts_and_kwargs_with_dict_overlaps(self):
        self.assertDictEqual(combine_dicts({1: 1, 2: 2, 3: 3}, {2: 4, 4: 5, 5: 3}, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 4, 3: 3, 4: 5, 5: 3})

    def test_dicts_and_kwargs_and_ignorables(self):
        self.assertDictEqual(combine_dicts({1: 1, 2: 2, 3: 3}, 5, 'the', None, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 2, 3: 3})


class TestGenDictKeyMatches(basetest.TestBase):
    def test_with_nested(self):
        self.checkEqual(list(gen_dict_key_matches('name', {1: 1, 2: 2, 3: 3, 'test': {'name': 'mesh',
                                                                                      'test': {'name': 'bah'}},
                                                           'name': 'test', 'discipline': 'lots'})),
                        ['mesh', 'bah', 'test'])

    def test_not_nested(self):
        self.assertListEqual(list(gen_dict_key_matches('name',
                                                       {1: 1, 2: 2, 3: 3, 'name': 'mesh', 'discipline': 'lots'})),
                             ['mesh'])

    def test_list(self):
        self.checkEqual(list(gen_dict_key_matches('name',
                                                  {1: 1, 2: 2, 3: 3, 'test': {'name': 'mesh',
                                                                              'test': {'name': 'bah'},
                                                                              'suffixes': {'name':
                                                                                               {'bah': 'fah'}}},
                                                   'list': [{'name': 'nested_list'}, 5]})),
                        ['mesh', 'bah', {'bah': 'fah'}, 'nested_list'])

    def test_empty(self):
        self.assertListEqual(list(gen_dict_key_matches('name', {})),
                             [])

    def test_simple(self):
        self.assertEquals(next(gen_dict_key_matches('test', {'test': 1})), 1)

    def test_simple_with_path(self):
        self.assertEquals(next(gen_dict_key_matches('test', {'test': 1}, full_path=True)), (['test'], 1))

    def test_list_full_path(self):
        self.checkEqual(list(gen_dict_key_matches('name',
                                                  {1: 1, 2: 2, 3: 3, 'test': {'name': 'mesh',
                                                                              'test': {'name': 'bah'},
                                                                              'suffixes': {'name':
                                                                                               {'bah': 'fah'}}},
                                                   'list': [{'name': 'nested_list'}, 5]},
                                                  full_path=True)),
                        ['mesh', 'bah', {'bah': 'fah'}, 'nested_list'])

    def test_mock_config_find(self):
        self.checkEqual(
            list(get_keys_containing('naming_formats', OrderedDict([('overall_config', {'version_padding': 3}),
                                                                    ('options', {
                                                                        'discipline': {
                                                                            'animation': 'AN ANI ANIM ANIMN',
                                                                            'lighting': 'LT LGT LGHT LIGHT',
                                                                            'compositing': 'CM CMP COMP COMPG',
                                                                            'rigging': 'RG RIG RIGG RIGNG',
                                                                            'modeling': 'MD MOD MODL MODEL',
                                                                            'matchmove': 'MM MMV MMOV MMOVE'},
                                                                        'side': ['left', 'right', 'center']}),
                                                                    ('naming_formats', {
                                                                        'node': {
                                                                            'default': 'side_location_nameDecoratorVar_childtype_purpose_type',
                                                                            'format_archive': 'side_name_space_purpose_decorator_childtype_type',
                                                                            'format_lee': 'type_childtype_space_purpose_name_side'},
                                                                        'texturing': {
                                                                            'shader': 'side_name_type'}})]))),
            ['node', 'texturing'])


class TestGetKeysContaining(basetest.TestBase):
    def test_simple(self):
        self.assertEquals(get_keys_containing('test', {'test': 1}), 1)

    def test_not_existing(self):
        self.assertEquals(get_keys_containing('mest', {'test': 1}), None)

    def test_mock_config_find(self):
        self.checkEqual(
            list(get_keys_containing('naming_formats', OrderedDict([('overall_config', {'version_padding': 3}),
                                                                    ('options', {
                                                                        'discipline': {'animation': 'AN ANI ANIM ANIMN',
                                                                                       'lighting': 'LT LGT LGHT LIGHT',
                                                                                       'compositing': 'CM CMP COMP COMPG',
                                                                                       'rigging': 'RG RIG RIGG RIGNG',
                                                                                       'modeling': 'MD MOD MODL MODEL',
                                                                                       'matchmove': 'MM MMV MMOV MMOVE'},
                                                                        'side': ['left', 'right', 'center']}),
                                                                    ('naming_formats', {
                                                                        'node': {
                                                                            'default': 'side_location_nameDecoratorVar_childtype_purpose_type',
                                                                            'format_archive': 'side_name_space_purpose_decorator_childtype_type',
                                                                            'format_lee': 'type_childtype_space_purpose_name_side'},
                                                                        'texturing': {'shader': 'side_name_type'}})]))),
            ['node', 'texturing'])
