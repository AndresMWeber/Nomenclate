# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import unittest
import itertools
import datetime
import nomenclate.core.nameparser as np

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
                    if self.fixture._valid_camel(permutation):
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
                        '%Y%m%d-%H%M',
                        '%Y']
        input_time = datetime.datetime(2016, 9, 16, 9, 30, 15)
        orders = ['hotel_minatorOutpost_{DATE}_1.5.mb',
                  'hotel_minatorOutpost_1.5.mb_{DATE}',
                  '{DATE}_hotel_minatorOutpost_1.5.mb',
                  '{DATE}.hotel_minatorOutpost_1.5.mb',
                  'hotel_minator{DATE}_tested_LOC',
                  'hotel_{DATE}minator_tested_LOC',
                  'hotel_blahbergG{DATE}minator_tested_LOC',
                  'hippydrome_{DATE}.fbx',
                  'IMG_{DATE}_140103743.jpg']

        for order in orders:
            for test_format in test_formats:
                self.assertEqual(self.fixture.get_date(order.format(DATE=input_time.strftime(test_format))),
                                 (datetime.datetime.strptime(input_time.strftime(test_format), test_format), test_format))

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
        self.assertEquals([i for i in self.fixture._get_abbrs('test', 2)], ['te', 'ts', 'tt'])

    def test_get_base_options(self):
        self.assertEquals(self.fixture.get_base('gus_clothing_v10_aw.ZPR')['basename'], 'gus_clothing')
        self.assertEquals(self.fixture.get_base('jacket_NORM.1004.tif')['basename'], 'jacket_NORM')
        self.assertEquals(self.fixture.get_base('jacket_substance_EXPORT.abc')['basename'], 'jacket_substance_EXPORT')
        self.assertEquals(self.fixture.get_base('27_12_2015')['basename'], None)
        self.assertEquals(self.fixture.get_base('clothing_compiled_maya_v01_aw.mb')['basename'], 'clothing_compiled_maya')
        self.assertEquals(self.fixture.get_base('QS_296.ZPR')['basename'], 'QS')
        self.assertEquals(self.fixture.get_base('char_luchadorA-model1_qt1.mov')['basename'], 'char_luchadorA-model_qt')
        self.assertEquals(self.fixture.get_base('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma')['basename'],
                          'kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin')
        self.assertEquals(self.fixture.get_base('rig_makeGentooPenguin.mel')['basename'], 'rig_makeGentooPenguin')
        self.assertEquals(self.fixture.get_base('r_foreLeg.obj')['basename'], 'foreLeg')
        self.assertEquals(self.fixture.get_base('samsung_galaxy_s6_rough.stl')['basename'], 'samsung_galaxy_s6_rough')
        self.assertEquals(self.fixture.get_base('mansur_gavriel_purse_back.stl')['basename'], 'mansur_gavriel_purse')
        self.assertEquals(self.fixture.get_base('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov')['basename'],
                          'sh01')
        self.assertEquals(self.fixture.get_base('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov')['basename'],
                          'Nesquik_Light_Sign')
        self.assertEquals(self.fixture.get_base('12301121_004_Nesquik_Light_Sign_Anim_Test.mov')['basename'],
                          'Nesquik_Light_Sign')
        self.assertEquals(self.fixture.get_base('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma')['basename'],
                          'nesquikQuicky_5402876_build_char_quicky')
        self.assertEquals(self.fixture.get_base('IMG_20160509_140103743.jpg')['basename'], 'IMG')
        self.assertEquals(self.fixture.get_base('hippydrome_2014.fbx')['basename'], 'hippydrome')
        self.assertEquals(self.fixture.get_base('AM152_FBX.part03.rar')['basename'], 'AM152_FBX')
        self.assertEquals(self.fixture.get_base('envelope_RB_v003_weights_groundhog.ma')['basename'], 'envelope')
        self.assertEquals(self.fixture.get_base('envelope_weights_02_unsmoothedJoints.json')['basename'], 'envelope_weights')
        self.assertEquals(self.fixture.get_base('icons_MDL_v006_aw.ma')['basename'], 'icons')
        self.assertEquals(self.fixture.get_base('moleV01.001.jpg')['basename'], 'mole')

    def test_get_version_options(self):
        self.assertEquals(self.fixture.get_version('gus_clothing_v10_aw.ZPR'), (10, ['v10']))
        self.assertEquals(self.fixture.get_version('jacket_NORM.1004.tif'), (1004, ['1004']))
        self.assertEquals(self.fixture.get_version('jacket_substance_EXPORT.abc'), None)
        self.assertEquals(self.fixture.get_version('27_12_2015'), None)
        self.assertEquals(self.fixture.get_version('clothing_compiled_maya_v01_aw.mb'), (1, ['v01']))
        self.assertEquals(self.fixture.get_version('QS_296.ZPR'), (296, ['296']))
        self.assertEquals(self.fixture.get_version('char_luchadorA-model1_qt1.mov'), (1.1, ['1', '1']))
        self.assertEquals(self.fixture.get_version('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma'), (2, ['v2']))
        self.assertEquals(self.fixture.get_version('rig_makeGentooPenguin.mel'), None)
        self.assertEquals(self.fixture.get_version('r_foreLeg.obj'), None)
        self.assertEquals(self.fixture.get_version('samsung_galaxy_s6_rough.stl'), None)
        self.assertEquals(self.fixture.get_version('mansur_gavriel_purse_back.stl'), None)
        self.assertEquals(self.fixture.get_version('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov'), (8.3, ['v8', 'v3']))
        self.assertEquals(self.fixture.get_version('Ne1004squik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov'), None)
        self.assertEquals(self.fixture.get_version('12301121_004_Nesquik_Light_Sign_Anim_Test.mov'), (4, ['004']))
        self.assertEquals(self.fixture.get_version('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma'), (10, ['v10']))
        self.assertEquals(self.fixture.get_version('IMG_20160509_140103743.jpg'), None)
        self.assertEquals(self.fixture.get_version('hippydrome_2014.fbx'), None)
        self.assertEquals(self.fixture.get_version('AM152_FBX.part03.rar'), (3, ['03']))
        self.assertEquals(self.fixture.get_version('envelope_RB_v003_weights_groundhog.ma'), (3, ['v003']))
        self.assertEquals(self.fixture.get_version('envelope_weights_02_unsmoothedJoints.json'), (2, ['02']))
        self.assertEquals(self.fixture.get_version('icons_MDL_v0006_aw.ma'), (6, ['v0006']))
        self.assertEquals(self.fixture.get_version('moleV01.001.jpg'), (1.1, ['V01', '001']))

    def test_get_udim_options(self):
        self.assertEquals(self.fixture.get_udim('gus_clothing_v10_aw.ZPR'),  None)
        self.assertEquals(self.fixture.get_udim('jacket_NORM.1004.tif'), 1004)
        self.assertEquals(self.fixture.get_udim('jacket_NORM1004.tif'), 1004)
        self.assertEquals(self.fixture.get_udim('jacket_NORM_1004_tif'), 1004)
        self.assertEquals(self.fixture.get_udim('jacket_NORM1004poop.tif'), None) # Deemed a shitty case, not handling it.
        self.assertEquals(self.fixture.get_udim('jacket_substance_EXPORT.abc'), None)
        self.assertEquals(self.fixture.get_udim('27_12_2015'), None)
        self.assertEquals(self.fixture.get_udim('QS_296.ZPR'), None)
        self.assertEquals(self.fixture.get_udim('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov'), None)
        self.assertEquals(self.fixture.get_udim('IMG_20160509_140103743.jpg'), None)

