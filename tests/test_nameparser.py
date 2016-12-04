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

    def test_get_side_camel(self):
        self._side_runner(['prefix_part%s_dir_type',
                           'prefix_%sPart_dir_type'])

    def test_get_side_no_side_present(self):
        self.assertEquals(self.fixture.get_side('blah_is_no_type_of_side_LOC'),
                          None)

    def test_side_edge_cases(self):
        tests = [('r_foreLeg.obj', ['right', (0, 2), 'r']),
                 ('jacket_substance_EXPORT.abc', None)]

        for test_string, test_value in tests:
            result = self.fixture.get_side(test_string)
            if result:
                result = [result[val] for val in ['side', 'position_full', 'match']]
            self.assertEquals(result, test_value)

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
                        tested_list = self.fixture.get_side(test_option % permutation)
                        if tested_list:
                            tested_list = [tested_list[val] for val in ['side', 'position_full', 'match']]

                        test_index = test_option.find('%s')-1
                        if permutation[0].islower() and test_option[test_index].isalpha() and test_index != -1:
                            self.assertIsNone(tested_list)
                        else:
                            for element in [side, permutation]:
                                self.assertIn(element, tested_list)

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
                result = self.fixture.get_date(order.format(DATE=input_time.strftime(test_format)))
                if result:
                    result = (result['datetime'], result['format'])
                self.assertEqual(result,
                                 (datetime.datetime.strptime(input_time.strftime(test_format), test_format), test_format))

    def test_valid_camel(self):
        for test in [('aAaa', True), ('Aaaa', False), ('AAAaaaaa', True), ('AAAAaaaAAA', True),
                     ('AaA', True), ('Aa', False), ('AA', False), ('aa', False), ('camel', False),
                     ('camelCase', True), ('CamelCase', True), ('CAMELCASE', False), ('camelcase', False),
                     ('Camelcase', False), ('Case', False), ('camelCamelCase', True)]:
            test, val = test
            print (test, val)
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
        # double checking shorter casing permutations...it fucks up on length two currently
        self.assertEquals([i for i in self.fixture._get_casing_permutations('lf')],
                          ['lf', 'Lf', 'lF', 'LF'])

    def test_get_abbrs_options(self):
        self.assertEquals([i for i in self.fixture._get_abbrs('test', 2)], ['te', 'ts', 'tt'])
        self.assertEquals([i for i in self.fixture._get_abbrs('test')], ['te', 'tes', 'test', 'ts', 'tst', 'tt', 't'])

    def test_get_base_options(self):
        self.assertEquals(self.fixture.get_base('gus_clothing_v10_aw.ZPR')['match'], 'gus_clothing')
        self.assertEquals(self.fixture.get_base('jacket_NORM.1004.tif')['match'], 'jacket_NORM')
        self.assertEquals(self.fixture.get_base('jacket_substance_EXPORT.abc')['match'], 'jacket_substance_EXPORT')
        self.assertEquals(self.fixture.get_base('27_12_2015'), None)
        self.assertEquals(self.fixture.get_base('clothing_compiled_maya_v01_aw.mb')['match'], 'clothing_compiled_maya')
        self.assertEquals(self.fixture.get_base('QS_296.ZPR')['match'], 'QS')
        self.assertEquals(self.fixture.get_base('char_luchadorA-model1_qt1.mov')['match'], 'char_luchadorA-model_qt')
        self.assertEquals(self.fixture.get_base('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma')['match'],
                          'kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin')
        self.assertEquals(self.fixture.get_base('rig_makeGentooPenguin.mel')['match'], 'rig_makeGentooPenguin')
        self.assertEquals(self.fixture.get_base('r_foreLeg.obj')['match'], 'foreLeg')
        self.assertEquals(self.fixture.get_base('samsung_galaxy_s6_rough.stl')['match'], 'samsung_galaxy_s6_rough')
        self.assertEquals(self.fixture.get_base('mansur_gavriel_purse_back.stl')['match'], 'mansur_gavriel_purse_back')
        self.assertEquals(self.fixture.get_base('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov')['match'],
                          'LSC_sh')
        self.assertEquals(self.fixture.get_base('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov')['match'],
                          'Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime')
        self.assertEquals(self.fixture.get_base('12302016_004_Nesquik_Light_Sign_Anim_Test.mov')['match'],
                          'Nesquik_Light_Sign_Anim_Test')
        self.assertEquals(self.fixture.get_base('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma')['match'],
                          'nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA')
        self.assertEquals(self.fixture.get_base('IMG_20160509_140103743.jpg')['match'], 'IMG')
        self.assertEquals(self.fixture.get_base('hippydrome_2014.fbx')['match'], 'hippydrome')
        self.assertEquals(self.fixture.get_base('AM152_FBX.part03.rar')['match'], 'AM152_FBX')
        self.assertEquals(self.fixture.get_base('envelope_RB_v003_weights_groundhog.ma')['match'], 'envelope_RB')
        self.assertEquals(self.fixture.get_base('envelope_weights_02_unsmoothedJoints.json')['match'], 'envelope_weights')
        self.assertEquals(self.fixture.get_base('icons_MDL_v006_aw.ma')['match'], 'icons_MDL')
        self.assertEquals(self.fixture.get_base('moleV01.001.jpg')['match'], 'mole')

    def test_get_version_options(self):
        tests = [('gus_clothing_v10_aw.ZPR', (10, 'v10')),
                 ('jacket_NORM.1004.tif', (1004, '1004')),
                 ('jacket_substance_EXPORT.abc', None),
                 ('27_12_2015', None),
                 ('clothing_compiled_maya_v01_aw.mb', (1, 'v01')),
                 ('QS_296.ZPR', (296, '296')),
                 ('char_luchadorA-model1_qt1.mov', ('1.1', '1')),
                 ('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma', (2, 'v2')),
                 ('rig_makeGentooPenguin.mel', None),
                 ('r_foreLeg.obj', None),
                 ('samsung_galaxy_s6_rough.stl', None),
                 ('mansur_gavriel_purse_back.stl', None),
                 ('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov', ('1.8.3', '01')),
                 ('Ne1004squik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov', None),
                 ('12301121_004_Nesquik_Light_Sign_Anim_Test.mov', (4, '004')),
                 ('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma', (10, 'v10')),
                 ('IMG_20160509_140103743.jpg', None),
                 ('hippydrome_2014.fbx', None),
                 ('AM152_FBX.part03.rar', (3, '03')),
                 ('envelope_RB_v003_weights_groundhog.ma', (3, 'v003')),
                 ('envelope_weights_02_unsmoothedJoints.json', (2, '02')),
                 ('icons_MDL_v0006_aw.ma', (6, 'v0006')),
                 ('moleV01.001.jpg', ('1.1', 'V01'))]

        for test, value in tests:
            test_result = self.fixture.get_version(test)
            if test_result is not None:
                version = test_result.get('version', None) or test_result.get('compound_version')
                match = test_result.get('match', None)
                try:
                    match = test_result.get('compound_matches')[0].get('match')
                except (IndexError, TypeError):
                    pass
                self.assertEquals((version, match), value)
            else:
                print (test_result)
                self.assertEquals(test_result, value)

    def test_get_udim_options(self):
        tests = [('gus_clothing_v10_aw.ZPR', None),
                 ('jacket_NORM.1004.tif', 1004),
                 ('jacket_NORM1004.tif', 1004),
                 ('jacket_NORM1004poop.tif', None), # Deemed a shitty case, not handling it.
                 ('jacket_substance_EXPORT.abc', None),
                 ('27_12_2015', None),
                 ('QS_296.ZPR', None),
                 ('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov', None),
                 ('IMG_20160509_140103743.jpg', None)]
        for test_string, test_value in tests:
            result = self.fixture.get_udim(test_string)
            if result:
                result = result['match_int']
            self.assertEquals(result, test_value)
