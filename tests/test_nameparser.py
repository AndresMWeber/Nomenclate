import unittest
import itertools
import datetime
import nomenclate.core.nameparser as np
from . import basetest


@unittest.skip
class TestNameparser(basetest.TestBase):
    def setUp(self):
        super(TestNameparser, self).setUp()
        self.fixture = np.NameParser()
        self.test_filenames = ['VGS15_sh004_lgt_v002.ma',
                               'vhcl_chevyTraverse_2018_interior_rig_v06_jf.ma',
                               'nurs_enchant_lilies_hi_cn_flowers_receptacle_a_1002_tg',
                               'HKY_010_lighting_v007.hip',
                               'Will_102_060',
                               'cdf0090_lighting_PROPS_FG_RIM_beauty_v011.1062.exr',
                               'I_HKY_150_L1_v1_graded.1001.jpeg',
                               'us.gcr.io_valued-geode-142207%2Fappengine_default.tar',
                               '12-09-16_theStuff_photo_post1s_b02.psd']

    def tearDown(self):
        super(TestNameparser, self).tearDown()
        del self.fixture

    def test_parse_options(self):
        self.assertEquals(self.fixture.parse_name(self.test_filenames[0])['basename']['match'], 'VGS15_sh_lgt')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[1])['basename']['match'], 'vhcl_chevyTraverse')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[2])['basename']['match'],
                          'nurs_enchant_lilies_hi')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[2])['side']['match'], 'cn')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[3])['basename']['match'], 'HKY')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[4])['basename']['match'], 'Will')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[5])['basename']['match'],
                          'cdf_lighting_PROPS_FG_RIM_beauty')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[6])['basename']['match'], 'I_HKY')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[7])['basename']['match'], 'us')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[8])['basename']['match'],
                          'theStuff_photo_post1s_b')
        self.assertEquals(self.fixture.parse_name(self.test_filenames[8])['version']['version'], 2)
        self.assertEquals(self.fixture.parse_name(self.test_filenames[8])['date']['match'], '12-09-16')

    def test_short_options(self):
        self.assertEqual(self.fixture.get_short('robotsLight8|robotLight2|robotLight2Shape'), 'robotLight2Shape')
        self.assertEqual(self.fixture.get_short('robotLight2Shape'), 'robotLight2Shape')
        self.assertEqual(self.fixture.get_short('robotsLight8|robotLight2|l_arm_up_LOC'), 'l_arm_up_LOC')

    def test_discipline_options_invalid(self):
        tests = ['gus_clothing_v10_aw.ZPR',
                 'Total_Protonic_reversal_v001_(Shane).exr',
                 'jacket_NORM.1004.tif',
                 'jacket_substance_EXPORT.abc',
                 '27_12_2015',
                 'clothing_compiled_maya_v01_aw.mb',
                 'QS_296.ZPR',
                 'r_foreLeg.obj',
                 'samsung_galaxy_s6_rough.stl',
                 'mansur_gavriel_purse_back.stl',
                 'LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov',
                 'IMG_20160509_140103743.jpg',
                 'hippydrome_2014.fbx', 'AM152_FBX.part03.rar',
                 'envelope_RB_v003_weights_groundhog.ma',
                 'envelope_weights_02_unsmoothedJoints.json',
                 'moleV01.001.jpg',
                 'robots8|robot2|robott2Shape']
        for test in tests:
            self.assertIsNone(self.fixture.get_discipline(test))

    def test_discipline_options_valid(self):
        tests = [('char_luchadorA-model1_qt1.mov', 'model'),
                 ('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma', 'rig'),
                 ('rig_makeGentooPenguin.mel', 'rig'),
                 ('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov', 'Anim'),
                 ('12302016_004_Nesquik_Light_Sign_Anim_Test.mov', 'Anim'),
                 ('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma', 'model'),
                 ('icons_MDL_v006_aw.ma', 'MDL')]
        for test, val in tests:
            self.assertEquals(self.fixture.get_discipline(test)['match'], val)

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
            for abbr in np.NameParser._get_abbreviations(side, 3):
                permutations = itertools.chain(permutations,
                                               np.NameParser._get_casing_permutations(abbr))

            for permutation in permutations:
                for test_option in test_options:
                    # Removing unlikely permutations like LeF: they could be mistaken for camel casing on other words
                    if self.fixture.is_valid_camel(permutation):
                        side_results = self.fixture.get_side(test_option % permutation)
                        if side_results:
                            side_results = [side_results[val] for val in ['side', 'position_full', 'match']]

                        test_index = test_option.find('%s') - 1
                        if permutation[0].islower() and test_option[test_index].isalpha() and test_index != -1:
                            self.assertIsNone(side_results)
                        else:
                            for element in [side, permutation]:
                                print(element, side_results)
                                self.assertIn(element, side_results)

    def test_get_date_specific(self):
        self.assertEquals(self.fixture.get_date('12-09-16_theStuff_photo_post1s_b02.psd')['match'], '12-09-16')

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
                                 (datetime.datetime.strptime(input_time.strftime(test_format), test_format),
                                  test_format))

    def test_valid_camel(self):
        for test in [('aAaa', True), ('Aaaa', False), ('AAAaaaaa', True), ('AAAAaaaAAA', True),
                     ('AaA', True), ('Aa', False), ('AA', False), ('aa', False), ('camel', False),
                     ('camelCase', True), ('CamelCase', True), ('CAMELCASE', False), ('camelcase', False),
                     ('Camelcase', False), ('Case', False), ('camelCamelCase', True)]:
            test, val = test
            print (test, val)
            self.assertEquals(self.fixture.is_valid_camel(test), val)

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
        self.assertEquals([i for i in self.fixture._get_abbreviations('test', 2)],
                          ['te', 'tes', 'test', 'ts', 'tst', 'tt'])
        self.assertEquals([i for i in self.fixture._get_abbreviations('test')],
                          ['te', 'tes', 'test', 'ts', 'tst', 'tt', 't'])

    def test_get_base_options(self):
        self.assertEquals(self.fixture.get_base('gus_clothing_v10_aw.ZPR')['match'], 'gus_clothing')
        self.assertEquals(self.fixture.get_base('jacket_NORM.1004.tif')['match'], 'jacket_NORM')
        self.assertEquals(self.fixture.get_base('jacket_substance_EXPORT.abc')['match'], 'jacket_substance_EXPORT')
        self.assertEquals(self.fixture.get_base('27_12_2015'), None)
        self.assertEquals(self.fixture.get_base('clothing_compiled_maya_v01_aw.mb')['match'], 'clothing_compiled_maya')
        self.assertEquals(self.fixture.get_base('QS_296.ZPR')['match'], 'QS')
        self.assertEquals(self.fixture.get_base('char_luchadorA-model1_qt1.mov')['match'], 'char_luchadorA-model_qt')
        self.assertEquals(
            self.fixture.get_base('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma')['match'],
            'kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin')
        self.assertEquals(self.fixture.get_base('rig_makeGentooPenguin.mel')['match'], 'rig_makeGentooPenguin')
        self.assertEquals(self.fixture.get_base('r_foreLeg.obj')['match'], 'foreLeg')
        self.assertEquals(self.fixture.get_base('samsung_galaxy_s6_rough.stl')['match'], 'samsung_galaxy_s_rough')
        self.assertEquals(self.fixture.get_base('mansur_gavriel_purse_back.stl')['match'], 'mansur_gavriel_purse_back')
        self.assertEquals(
            self.fixture.get_base('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_032415-540p_Quicktime.mov')['match'],
            'LSC_sh')
        self.assertEquals(self.fixture.get_base('Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov')['match'],
                          'Nesquik_Light_Sign_Anim_Test-1080p_HD_Quicktime')
        self.assertEquals(self.fixture.get_base('12302016_004_Nesquik_Light_Sign_Anim_Test.mov')['match'],
                          'Nesquik_Light_Sign_Anim_Test')
        self.assertEquals(
            self.fixture.get_base('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma')['match'],
            'nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA')
        self.assertEquals(self.fixture.get_base('IMG_20160509_140103743.jpg')['match'], 'IMG')
        self.assertEquals(self.fixture.get_base('hippydrome_2014.fbx')['match'], 'hippydrome')
        self.assertEquals(self.fixture.get_base('AM152_FBX.part03.rar')['match'], 'AM152_FBX')
        self.assertEquals(self.fixture.get_base('envelope_RB_v003_weights_groundhog.ma')['match'], 'envelope_RB')
        self.assertEquals(self.fixture.get_base('envelope_weights_02_unsmoothedJoints.json')['match'],
                          'envelope_weights')
        self.assertEquals(self.fixture.get_base('icons_MDL_v006_aw.ma')['match'], 'icons_MDL')
        self.assertEquals(self.fixture.get_base('moleV01.001.jpg')['match'], 'mole')

    def test_get_version_options(self):
        tests = [('gus_clothing_v10_aw.ZPR', (10, 'v10')),
                 ('jacket_NORM.1004.tif', (1004, '1004')),
                 ('jacket_substance_EXPORT.abc', None),
                 ('27_12_2015', None),
                 ('clothing_compiled_maya_v01_aw.mb', (1, 'v01')),
                 ('QS_296.ZPR', (296, '296')),
                 ('char_luchadorA-model1_qt1.mov', (1.1, '1')),
                 ('kayJewelersPenguin_5402411_build_penguin_rigPuppet_penguin_v2.ma', (2, 'v2')),
                 ('rig_makeGentooPenguin.mel', None),
                 ('r_foreLeg.obj', None),
                 ('samsung_galaxy_s6_rough.stl', (6, '6')),
                 ('mansur_gavriel_purse_back.stl', None),
                 ('LSC_sh01_v8_Nesquick_SFX_MS\-_WIP_v3_032415-540p_Quicktime.mov', ('1.8.3', '01')),
                 ('Ne1004squik_Light_Sign_Anim_Test-1080p_HD_Quicktime.mov', None),
                 ('12301121_004_Nesquik_Light_Sign_Anim_Test.mov', (4, '004')),
                 ('nesquikQuicky_5402876_build_char_quicky_model_quicky_lodA_v10.ma', (10, 'v10')),
                 ('IMG_20160509_140103743.jpg', None),
                 ('hippydrome_2014.fbx', None),
                 ('AM152_FBX.part03.rar', (3, '03')),
                 ('envelope_RB_v003_weights_groundhog.ma', (3, 'v003')),
                 ('envelope_weights_02_unsmoothedJoints.json', (2, '02')),
                 ('icons_MDL_v0006_aw.ma', (6, 'v0006')),
                 ('moleV01.001.jpg', (1.1, 'V01')),
                 ('VGS15_sh004_lgt_v002', (4.2, '004'))]

        for test, value in tests:
            test_result = self.fixture.get_version(test)
            if test_result is not None:
                version = test_result.get('version', None) or test_result.get('compound_version')
                match = test_result.get('match', None)
                try:
                    match = test_result.get('compound_matches')[0].get('match')
                except (IndexError, TypeError):
                    pass
                print (test_result)
                self.assertEquals((version, match), value)
            else:
                self.assertEquals(test_result, value)

    def test_get_udim_options(self):
        tests = [('gus_clothing_v10_aw.ZPR', None),
                 ('jacket_NORM.1004.tif', 1004),
                 ('jacket_NORM1004.tif', 1004),
                 ('jacket_NORM1004poop.tif', None),  # Deemed a shitty case, not handling it.
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
