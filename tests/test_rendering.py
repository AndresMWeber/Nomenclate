from six import iteritems
import re
import nomenclate.core.rendering as nm
import nomenclate.core.errors as ex
import nomenclate.core.nomenclature as nc
from . import basetest


class TestNomenclativeBase(basetest.TestBase):
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


class TokenMatchBase(basetest.TestBase):
    def setUp(self):
        super(TokenMatchBase, self).setUp()
        self.regex_custom_group_match = next(re.compile(r'(?P<look>test)').finditer('test'))

        test_re_matches = re.compile(r'(?P<token>te)').finditer('test')
        self.token_match_start = nm.TokenMatch(next(test_re_matches), 'mx', group_name='token')

        test_re_matches = re.compile(r'(?P<token>es)').finditer('test')
        self.token_match_mid = nm.TokenMatch(next(test_re_matches), 'lz', group_name='token')

        test_re_matches = re.compile(r'(?P<token>st)').finditer('test')
        self.token_match_end = nm.TokenMatch(next(test_re_matches), 'fr', group_name='token')

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
        self.assertRaises(ex.OverlapError, self.token_match_start.adjust_position, self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(IOError, self.token_match_start.adjust_position, 5)


class TestInputRendererBase(TestNomenclativeBase):
    def setUp(self):
        super(TestInputRendererBase, self).setUp()
        self.ir = nm.InputRenderer
        self.nom = nc.Nomenclate()
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.nom.var.set('A')
        self.fixtures.append([self.ir, self.nom])


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
                          {'var': 'A', 'type': 'LOC', 'side': 'l', 'version': 'v005'})

    def test_some_replaced(self):
        test_values = {'var': 'A', 'type': 'locator', 'side': 'left', 'version': 5}
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {'var': 'A', 'type': 'LOC', 'side': 'l', 'version': 'v005'})

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
