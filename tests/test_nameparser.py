# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import re
import unittest
import itertools
import nomenclate.core.nameparser as np
from nomenclate.core.nameparser import datetime

reload(np)

__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"


class TestNameparser(unittest.TestCase):
    def setUp(self):
        self.fixture = np.NameParser()

    def tearDown(self):
        del self.fixture

    def test_short_options(self):
        self.assertEqual(self.fixture.get_short('robotsLight8|robotLight2|robotLight2Shape'), 'robotLight2Shape')
        self.assertEqual(self.fixture.get_short('robotLight2Shape'), 'robotLight2Shape')
        self.assertEqual(self.fixture.get_short('robotsLight8|robotLight2|l_arm_up_LOC'), 'l_arm_up_LOC')

    def test_get_side_options(self):
        # Testing for isolated by underscores
        self._side_runner(['%s_arm_up_LOC',
                           'prefix_%s_part_dir_type',
                           'prefix_part_up_%s'])

    def test_get_side_combined(self):
        self._side_runner(['prefix_part%s_dir_type',
                           'prefix_%sPart_dir_type'])

    def test_get_side_no_side_present(self):
        self.assertEquals(self.fixture.get_side('blah_is_no_type_of_side_LOC'),
                          None)

    def _side_runner(self, test_options):
        for side in ['left', 'right']:
            permutations = []
            for abbr in np.NameParser._get_abbrs(side):
                permutations = itertools.chain(permutations,
                                               np.NameParser._get_casing_permutations(abbr))
            for permutation in permutations:
                for test_option in test_options:
                    # Removing unlikely permutations like LeF: they could be mistaken for camel casing on other words
                    if re.findall('^([A-Z]+[a-z]*)(?![A-Z])$', permutation):
                        self.assertEquals(self.fixture.get_side(test_option % permutation), [side, permutation])

    def test_get_date_options(self):
        test_formats = ['%Y-%m-%d_%H-%M-%S',
                        '%Y-%m-%d-%H-%M-%S',
                        '%Y-%m-%d--%H-%M-%S',
                        '%Y-%m-%d%H-%M-%S',
                        '%Y-%m-%d',
                        '%m_%d_%Y',
                        '%m_%d_%y',
                        '%m%d%y',
                        '%m%d%Y',
                        '%y_%m_%dT%H_%M_%S',
                        '%Y%m%d',
                        '%Y%m%d-%H%M%S',
                        '%Y%m%d-%H%M']
        input_time = datetime.datetime(2016, 9, 16, 9, 30, 15)
        orders = ['hotel_minatorOutpost_{DATE}_1.5.mb',
                  'hotel_minatorOutpost_1.5.mb_{DATE}',
                  '{DATE}_hotel_minatorOutpost_1.5.mb',
                  '{DATE}.hotel_minatorOutpost_1.5.mb',
                  'hotel_minator{DATE}_tested_LOC',
                  'hotel_{DATE}minator_tested_LOC',
                  'hotel_blahbergG{DATE}minator_tested_LOC']

        for order in orders:
            for test_format in test_formats:
                self.assertEqual(self.fixture.get_date(order.format(DATE=input_time.strftime(test_format))),
                                 datetime.datetime.strptime(input_time.strftime(test_format), test_format))

    def test_valid_camel(self):
        for test in [('aAaa', False), ('Aaaa', True), ('AAAaaaaa',True), ('AAAAaaaAAA', False),
                     ('AaA', False), ('Aa', True), ('AA', True), ('aa', False)]:
            test, val = test
            self.assertEquals(self.fixture._valid_camel(test), val)

    def test_get_casing_permutations(self):
        # testing all possible permutations of a simple example
        self.assertEquals([i for i in self.fixture._get_casing_permutations('asdf')],
                          ['asdf', 'Asdf', 'aSdf', 'ASdf',
                           'asDf', 'AsDf', 'aSDf', 'ASDf',
                           'asdF', 'AsdF', 'aSdF', 'ASdF',
                           'asDF', 'AsDF', 'aSDF', 'ASDF'])
        # making sure it gives same results regardless of casing of original word
        self.assertEquals([i for i in self.fixture._get_casing_permutations('AfdS')],
                          [i for i in self.fixture._get_casing_permutations('Afds')])

    def test_get_abbrs_options(self):
        self.assertEquals([i for i in self.fixture._get_abbrs('test', 2)],
                          ['te', 'ts', 'tt'])

    def test_get_base_options(self):
        self.fixture.get_base('test')