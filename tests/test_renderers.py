import nomenclate.core.rendering as rendering
import nomenclate.core.renderers as renderers
import nomenclate.core.processing as processing
import nomenclate.core.tokens as tokens
import nomenclate.core.nomenclature as nom
from . import basetest


class TestRenderersBase(basetest.TestBase):
    def setUp(self):
        super(TestRenderersBase, self).setUp()
        self.nomenclative_valid = processing.Nomenclative('side_location_nameDecoratorVar_childtype_purpose_type')
        self.nomenclative_valid_short = processing.Nomenclative('side_name_type')
        self.nomenclative_invalid = processing.Nomenclative('test_labelside')

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


class TestInputRendererBase(TestRenderersBase):
    def setUp(self):
        super(TestInputRendererBase, self).setUp()
        self.ir = rendering.InputRenderer
        self.nom = nom.Nomenclate()
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.nom.var.set('A')
        self.fixtures.append([self.ir, self.nom])


class TestInputRendererProcessTokenAugmentations(TestInputRendererBase):
    def test_from_nomenclate_upper(self):
        self.nom.side.case = 'upper'
        self.assertEquals(self.nom.get(),
                          'L_testObjectA_LOC')

    def test_from_nomenclate_lower(self):
        self.nom.side.case = 'lower'
        self.assertEquals(self.nom.get(),
                          'l_testObjectA_LOC')

    def test_from_upper(self):
        token_attr = tokens.TokenAttr('test', 'name')
        token_attr.case = 'upper'
        self.assertEquals(renderers.RenderBase.process_token_augmentations('test', token_attr),
                          'TEST')

    def test_from_lower(self):
        token_attr = tokens.TokenAttr('test', 'name')
        token_attr.case = 'lower'
        self.assertEquals(renderers.RenderBase.process_token_augmentations('Test', token_attr),
                          'test')

    def test_from_none(self):
        token_attr = tokens.TokenAttr('test', 'name')
        self.assertEquals(renderers.RenderBase.process_token_augmentations('Test', token_attr),
                          'Test')

    def test_from_prefix(self):
        token_attr = tokens.TokenAttr('test', 'name')
        token_attr.prefix = 'v'
        self.assertEquals(renderers.RenderBase.process_token_augmentations('Test', token_attr),
                          'vTest')

    def test_from_suffix(self):
        token_attr = tokens.TokenAttr('test', 'name')
        token_attr.suffix = '_r'
        self.assertEquals(renderers.RenderBase.process_token_augmentations('test', token_attr),
                          'test_r')


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
        self.assertEquals(renderers.RenderVar._get_variation_id(0), 'a')

    def test_get_variation_id_negative(self):
        self.assertEquals(renderers.RenderVar._get_variation_id(-4), '')

    def test_get_variation_id_negative_one(self):
        self.assertEquals(renderers.RenderVar._get_variation_id(-1), '')

    def test_get_variation_id_double_upper(self):
        self.assertEquals(renderers.RenderVar._get_variation_id(1046, capital=True), 'ANG')

    def test_get_variation_id_double_lower(self):
        self.assertEquals(renderers.RenderVar._get_variation_id(1046, capital=False), 'ang')


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

    def test_default_renderer(self):
        test_values = {'var': 'A',
                       'type': 'locator',
                       'side': 'left',
                       'version': 5,
                       'john': 'six',
                       'purpose': 'hierarchy'}

        self.nom.format = self.nom.format + '_john'
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {'var': 'A',
                           'type': 'LOC',
                           'side': 'l',
                           'version': 'v005',
                           'john': 'six',
                           'purpose': 'hrc'})

    def test_empty(self):
        test_values = {}
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values,
                          {})

    def test_none_replaced(self):
        test_values = {'name': 'test', 'blah': 'marg', 'not_me': 'haha', 'la': 5}
        self.nom.merge_dict(test_values)
        test_values_unchanged = test_values.copy()
        test_values_unchanged['la'] = '5'
        self.ir.render_unique_tokens(self.nom, test_values)
        self.assertEquals(test_values, test_values_unchanged)
