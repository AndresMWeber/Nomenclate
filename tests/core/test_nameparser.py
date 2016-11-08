import unittest
import nomenclate.core.nameparser as np
from nomenclate.core.nameparser.datetime import datetime as datetime
reload(np)


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
        test_options = ''
        self.assertEqual(self.fixture.get_side('l_arm_up_LOC'), 'left')
        self.assertEqual(self.fixture.get_side('r_arm_up_LOC'), 'right')
        self.assertEqual(self.fixture.get_side('R_arm_up_LOC'), 'right')
        self.assertEqual(self.fixture.get_side('L_arm_up_LOC'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_l_part_dir_type'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_left_part_dir_type'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_lt_part_dir_type'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_le_part_dir_type'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_R_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_r_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_RGT_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_RgT_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_Rgt_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_rgt_part_dir_type'), 'right')
        self.assertEqual(self.fixture.get_side('prefix_part_dir_type_l'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_part_dir_type_lf'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_part_dir_type_LF'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_part_dir_type_left'), 'left')
        self.assertEqual(self.fixture.get_side('prefix_part_dir_type_right'), 'right')

    def test_get_base_options(self):
        self.assertEqual()

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
        input_time = datetime(2016, 9, 16, 9, 30, 15)
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
        self.assertEqual()