# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from future.utils import iteritems
import unittest
import re
import nomenclate.core.nomenclative as nm
import nomenclate.core.exceptions as ex


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
        self.assertRaises(ex.OverlapError, self.token_match_start.adjust_position, self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(IOError, self.token_match_start.adjust_position, 5)