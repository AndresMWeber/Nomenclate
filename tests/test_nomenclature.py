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


class TestNomenclativeBase(TestBase):
    def setUp(self):
        super(TestNomenclativeBase, self).setUp()

        self.nomenclative_valid = nm.Nomenclative('side_location_nameDecoratorVar_childtype_purpose_type')
        self.nomenclative_valid_short = nm.Nomenclative('side_name_type')
        self.nomenclative_invalid = nm.Nomenclative('test_labelside')

        self.token_test_dict = {'side': 'left',
                                'location': 'rear',
                                'name': 'test',
                                'decorator': '',
                                'var': 'A',
                                'childtype': 'joints',
                                'purpose': 'offset',
                                'type': 'group'}

        self.fixtures.append([self.nomenclative_valid,
                              self.nomenclative_valid_short,
                              self.nomenclative_invalid,
                              self.token_test_dict])


class TestNomenclativeProcessMatches(TestNomenclativeBase):
    def test_valid(self):
        test_dict = self.token_test_dict.copy()
        nm.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid.str)
        for token, value in iteritems(test_dict):
            self.nomenclative_valid.add_match(*value)
        self.assertEquals(self.nomenclative_valid.process_matches(),
                          'left_rear_testA_joints_offset_group')

    def test_valid_short(self):
        test_dict = self.token_test_dict.copy()
        nm.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid_short.str)
        print(test_dict)
        for token, value in iteritems(test_dict):
            if isinstance(value, str):
                pass
            else:
                self.nomenclative_valid_short.add_match(*value)
        self.assertEquals(self.nomenclative_valid_short.process_matches(),
                          'left_test_group')

    def test_invalid(self):
        self.assertEquals(self.nomenclative_invalid.process_matches(),
                          self.nomenclative_invalid.str)


class TestNomenclativeAddMatch(TestNomenclativeBase):
    def test_valid(self):
        test_dict = self.token_test_dict.copy()
        nm.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid.str)
        for token, value in iteritems(test_dict):
            self.nomenclative_valid.add_match(*value)
        self.assertEquals(self.nomenclative_valid.process_matches(),
                          'left_rear_testA_joints_offset_group')

    def test_overlap(self):
        test_dict = self.token_test_dict.copy()
        nm.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid_short.str)
        print(test_dict)
        for token, value in iteritems(test_dict):
            if not isinstance(value, str):
                self.nomenclative_valid_short.add_match(*value)
        self.assertEquals(self.nomenclative_valid_short.process_matches(),
                          'left_test_group')

    def test_non_regex_match_object(self):
        self.assertEquals(self.nomenclative_invalid.process_matches(),
                          self.nomenclative_invalid.str)


class TokenMatchBase(TestBase):
    def setUp(self):
        super(TokenMatchBase, self).setUp()
        self.regex_custom_group_match = next(re.compile(r'(?P<look>test)').finditer('test'))

        test_re_matches = re.compile(r'(?P<token>te)').finditer('test')
        self.token_match_start = nm.TokenMatch(test_re_matches.next(), 'mx', group_name='token')

        test_re_matches = re.compile(r'(?P<token>es)').finditer('test')
        self.token_match_mid = nm.TokenMatch(test_re_matches.next(), 'lz', group_name='token')

        test_re_matches = re.compile(r'(?P<token>st)').finditer('test')
        self.token_match_end = nm.TokenMatch(test_re_matches.next(), 'fr', group_name='token')

        self.fixtures.extend([self.token_match_start,
                              self.token_match_mid,
                              self.token_match_end])


class TokenMatchInit(TokenMatchBase):
    def test_missing_group(self):
        self.assertRaises(IndexError, nm.TokenMatch, self.regex_custom_group_match, 'marg')

    def test_group_custom(self):
        nm.TokenMatch(self.regex_custom_group_match, 'marg', group_name='look')


class TokenMatchContains(TokenMatchBase):
    def test_does_not_contain(self):
        self.assertFalse(self.token_match_start in self.token_match_end)

    def test_contains(self):
        self.assertTrue(self.token_match_start in self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(NotImplementedError, self.token_match_start.__contains__, 5)


class TokenMatchEquals(TokenMatchBase):
    def test_equal(self):
        self.assertTrue(self.token_match_start,
                        nm.TokenMatch(next(re.compile(r'(?P<token>te)').finditer('test')), 'mx'))

    def test_inequal(self):
        self.assertTrue(self.token_match_start,
                        self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(NotImplementedError, self.token_match_start.__eq__, 5)


class TokenMatchAdjustPosition(TokenMatchBase):
    def test_valid_adjust_alongside(self):
        test_re_matches = re.compile(r'(?P<token>st)').finditer('test')
        token_match_end = nm.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_end(self):
        test_re_matches = re.compile(r'(?P<token>er)').finditer('tester')
        token_match_end = nm.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_double(self):
        test_re_matches = re.compile(r'(?P<token>te)').finditer('lesterte')
        token_match_end = nm.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_no_move(self):
        self.assertRaises(IndexError, self.token_match_start.adjust_position, self.token_match_end)

    def test_invalid_adjust(self):
        self.assertRaises(IndexError, self.token_match_start.adjust_position, self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(IOError, self.token_match_start.adjust_position, 5)


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
        self.fixtures = [self.cfg, self.nom, self.test_format_b, self.test_format]


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
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

        self.nom.initialize_format_options(self.test_format)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

    def test_switch_naming_format_from_config(self):
        self.nom.initialize_format_options(['naming_formats', 'node', 'format_lee'])
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
        self.assertEquals(self.nom.format_string_object.get_format_order(self.test_format),
                          ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type'])


class TestNomenclateGet(TestNomenclateBase):
    def test_get(self):
        self.assertEquals(self.nom.get(), 'left_testObjectA_LOC')

    def test_get_after_change(self):
        previous_state = self.nom.state
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'left_rear_testObjectA_LOC')
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
    def test__repr__(self):
        self.assertEquals(self.nom.__repr__(), 'l_testObjectA_LOC')


class TestInputRendererBase(TestNomenclateBase):
    def setUp(self):
        super(TestInputRendererBase, self).setUp()
        self.ir = nm.InputRenderer
        self.fixtures.append(self.ir)


class TestInputRendererGetAlphanumericIndex(TestInputRendererBase):
    def test_get__get_alphanumeric_index_integer(self):
        self.assertEquals(self.ir._get_alphanumeric_index(0),
                          [0, 'int'])

    def test_get__get_alphanumeric_index_char_start(self):
        self.assertEquals(self.ir._get_alphanumeric_index('a'),
                          [0, 'char_lo'])

    def test_get__get_alphanumeric_index_char_end(self):
        self.assertEquals(self.ir._get_alphanumeric_index('z'),
                          [25, 'char_lo'])

    def test_get__get_alphanumeric_index_char_upper(self):
        self.assertEquals(self.ir._get_alphanumeric_index('B'),
                          [1, 'char_hi'])

    def test_get__get_alphanumeric_index_error(self):
        self.assertRaises(IOError, self.ir._get_alphanumeric_index, 'asdf')


class TestInputRendererCleanupFormattingString(TestInputRendererBase):
    def test_cleanup_format(self):
        self.assertEquals(self.ir.cleanup_formatted_string('test_name _messed __ up LOC'),
                          'test_name_messed_upLOC')


class TestInputRendererGetVariationId(TestInputRendererBase):
    def test_get_variation_id_normal(self):
        self.assertEquals(nm.RenderVar._get_variation_id(0), 'a')

    def test_get_variation_id_negative(self):
        self.assertEquals(nm.RenderVar._get_variation_id(-4), '')

    def test_get_variation_id_negative_one(self):
        self.assertEquals(nm.RenderVar._get_variation_id(-1), '')

    def test_get_variation_id_double_upper(self):
        self.assertEquals(nm.RenderVar._get_variation_id(1046, capital=True), 'ANG')

    def test_get_variation_id_double_lower(self):
        self.assertEquals(nm.RenderVar._get_variation_id(1046, capital=False), 'ang')


class TestInputRendererRenderUniqueTokens(TestInputRendererBase):
    def test_all_replaced(self):
        test_values = {'var': 'A', 'type': 'locator', 'side': 'left', 'version': 5}
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {'var': 'A', 'type': 'LOC', 'side': 'l', 'version': '005'})

    def test_some_replaced(self):
        test_values = {'var': 'A', 'type': 'locator', 'side': 'left', 'version': 5}
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {'var': 'A', 'type': 'locator', 'side': 'left', 'version': '005'})

    def test_empty(self):
        test_values = {}
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {})

    def test_none_replaced(self):
        test_values = {'name': 'test', 'blah': 'marg', 'not_me': 'haha', 'la': 5}
        test_values_unchanged = test_values.copy()
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values, test_values_unchanged)


class TestFormatStringBase(TestBase):
    def setUp(self):
        super(TestFormatStringBase, self).setUp()
        self.fs = nm.FormatString()
        self.fixtures.append(self.fs)


class TestFormatStringValidateFormatString(TestFormatStringBase):
    def test_get__validate_format_string_valid(self):
        self.fs._validate_format_string('side_mide')

    def test_get__validate_format_string__is_format_invalid(self):
        self.assertRaises(exceptions.FormatError, self.fs._validate_format_string('notside'))


class TestCombineDicts(TestBase):
    def test_with_dict_with_nomenclate_object(self):
        self.assertDictEqual(nm.combine_dicts({1: 1, 2: 2, 3: 3}, nm.Nomenclate(name='test', discipline='lots')),
                             {1: 1, 2: 2, 3: 3, 'name': 'test', 'discipline': 'lots'})

    def test_only_dicts(self):
        self.assertDictEqual(nm.combine_dicts({1: 1, 2: 2, 3: 3}, {4: 4, 5: 5, 6: 6}),
                             {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6})

    def test_no_dicts_or_kwargs(self):
        self.assertDictEqual(nm.combine_dicts('five', 5, None, [], 'haha'),
                             {})

    def test_kwargs(self):
        self.assertDictEqual(nm.combine_dicts(parse='test', plush=5),
                             {'parse': 'test', 'plush': 5})

    def test_dicts_and_kwargs(self):
        self.assertDictEqual(nm.combine_dicts({1: 1, 2: 2, 3: 3}, {4: 4, 5: 5, 6: 6}, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6})

    def test_dicts_and_kwargs_with_dict_overlaps(self):
        self.assertDictEqual(nm.combine_dicts({1: 1, 2: 2, 3: 3}, {2: 4, 4: 5, 5: 3}, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 4, 3: 3, 4: 5, 5: 3})

    def test_dicts_and_kwargs_and_ignorables(self):
        self.assertDictEqual(nm.combine_dicts({1: 1, 2: 2, 3: 3}, 5, 'the', None, parse='test', plush=5),
                             {'parse': 'test', 'plush': 5, 1: 1, 2: 2, 3: 3})


class TestGenDictExtract(TestBase):
    def test_with_nested(self):
        self.checkEqual(list(nm.gen_dict_key_matches('name', {1: 1, 2: 2, 3: 3, 'test': {'name': 'mesh',
                                                                                         'test': {'name': 'bah'}},
                                                              'name': 'test', 'discipline': 'lots'})),
                        ['mesh', 'bah', 'test'])

    def test_not_nested(self):
        self.assertListEqual(list(nm.gen_dict_key_matches('name',
                                                          {1: 1, 2: 2, 3: 3, 'name': 'mesh', 'discipline': 'lots'})),
                             ['mesh'])

    def test_list(self):
        self.checkEqual(list(nm.gen_dict_key_matches('name',
                                                     {1: 1, 2: 2, 3: 3, 'test': {'name': 'mesh',
                                                                                 'test': {'name': 'bah'},
                                                                                 'suffixes': {'name':
                                                                                                  {'bah': 'fah'}}},
                                                      'list': [{'name': 'nested_list'}, 5]})),
                        ['mesh', 'bah', {'bah': 'fah'}, 'nested_list'])

    def test_empty(self):
        self.assertListEqual(list(nm.gen_dict_key_matches('name', {})),
                             [])
