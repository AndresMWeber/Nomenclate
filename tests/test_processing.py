import re
import nomenclate.core.processing as processing
import nomenclate.core.errors as exceptions
from . import basetest


class TokenMatchBase(basetest.TestBase):
    def setUp(self):
        super(TokenMatchBase, self).setUp()
        self.regex_custom_group_match = next(re.compile(r'(?P<look>test)').finditer('test'))

        test_re_matches = re.compile(r'(?P<token>te)').finditer('test')
        self.token_match_start = processing.TokenMatch(next(test_re_matches), 'mx', group_name='token')

        test_re_matches = re.compile(r'(?P<token>es)').finditer('test')
        self.token_match_mid = processing.TokenMatch(next(test_re_matches), 'lz', group_name='token')

        test_re_matches = re.compile(r'(?P<token>st)').finditer('test')
        self.token_match_end = processing.TokenMatch(next(test_re_matches), 'fr', group_name='token')

        self.fixtures.extend([self.token_match_start,
                              self.token_match_mid,
                              self.token_match_end])


class TokenMatchInit(TokenMatchBase):
    def test_missing_group(self):
        self.assertRaises(IndexError, processing.TokenMatch, self.regex_custom_group_match, 'marg')

    def test_group_custom(self):
        processing.TokenMatch(self.regex_custom_group_match, 'marg', group_name='look')


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
                        processing.TokenMatch(next(re.compile(r'(?P<token>te)').finditer('test')), 'mx'))

    def test_inequal(self):
        self.assertTrue(self.token_match_start,
                        self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(NotImplementedError, self.token_match_start.__eq__, 5)


class TokenMatchGT(TokenMatchBase):
    def test_equal(self):
        self.assertFalse(self.token_match_start >
                         processing.TokenMatch(next(re.compile(r'(?P<token>te)').finditer('test')), 'mx'))

    def test_inequal(self):
        self.assertFalse(self.token_match_mid > self.token_match_start)

    def test_invalid_type(self):
        self.assertRaises(NotImplementedError, self.token_match_start.__gt__, 5)


class TokenMatchLT(TokenMatchBase):
    def test_equal(self):
        self.assertFalse(self.token_match_start <
                         processing.TokenMatch(next(re.compile(r'(?P<token>te)').finditer('test')), 'mx'))

    def test_inequal(self):
        self.assertFalse(self.token_match_start < self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(NotImplementedError, self.token_match_start.__lt__, 5)


class TokenMatchAdjustPosition(TokenMatchBase):
    def test_valid_adjust_alongside(self):
        test_re_matches = re.compile(r'(?P<token>st)').finditer('test')
        token_match_end = processing.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_end(self):
        test_re_matches = re.compile(r'(?P<token>er)').finditer('tester')
        token_match_end = processing.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_double(self):
        test_re_matches = re.compile(r'(?P<token>te)').finditer('lesterte')
        token_match_end = processing.TokenMatch(next(test_re_matches), 'fl', group_name='token')
        orig_start = token_match_end.start
        token_match_end.adjust_position(self.token_match_start, adjust_by_sub_delta=False)
        self.assertEquals(token_match_end.start,
                          orig_start - self.token_match_start.span)

    def test_valid_adjust_no_move(self):
        self.assertRaises(IndexError, self.token_match_start.adjust_position, self.token_match_end)

    def test_invalid_adjust(self):
        self.assertRaises(exceptions.OverlapError, self.token_match_start.adjust_position, self.token_match_mid)

    def test_invalid_type(self):
        self.assertRaises(IOError, self.token_match_start.adjust_position, 5)
