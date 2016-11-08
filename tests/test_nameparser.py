import unittest
import nomenclate.core.nameparser as np
import nomenclate.core.nameparser.datetime as datetime
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
        test_options = ['%s_arm_up_LOC',
                        'prefix_%s_part_dir_type',
                        'prefix_part%s_dir_type',
                        'prefix_%spart_dir_type',
                        'prefix_part_up_%s']

        for side in ['left', 'right']:
            permutations = np.NameParser._get_casing_permutations(np.NameParser._get_abbrs(side))
            for permutation in permutations:
                for test_option in test_options:
                    self.assertEquals(self.fixture.get_side(test_option % permutation), side)

    def test_get_base_options(self):
        pass

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
                self.assertEqual(self.fixture.get_date(order.format(input_time.strftime(test_format))),
                                 input_time)

    def test_get_abbr_options(self):
        pass