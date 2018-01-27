from six import iteritems
import unittest
import nomenclate as nm
import nomenclate.core.configurator as config
from tests.basetest import TestBase


class TestNomenclateBase(TestBase):
    def setUp(self):
        super(TestNomenclateBase, self).setUp()
        self.cfg = config.ConfigParse()
        self.test_format = 'side_location_nameDecoratorVar_childtype_purpose_type'
        self.test_format_b = 'location_nameDecoratorVar_childtype_purpose_type_side'

        self.nom = nm.Nom()

        # Inject our fake config
        self.nom.cfg = self.cfg
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.nom.var.set(0)
        self.nom.var.case = 'upper'
        self.fixtures = [self.cfg, self.nom, self.test_format_b, self.test_format]

    @property
    def fill_vars(self):
        return {'childtype': 'token',
                'purpose': 'filler',
                'side': 'left',
                'var': 0,
                'location': 'top',
                'type': 'locator',
                'name': 'testObject',
                'decorator': 'joint'}

    @property
    def empty_vars(self):
        return {'var': '',
                'type': '',
                'name': '',
                'location': '',
                'decorator': '',
                'side': '',
                'purpose': '',
                'childtype': ''}

    @property
    def partial_vars(self):
        return {'side': 'left',
                'var': 0,
                'type': 'locator',
                'name': 'testObject'}

    @property
    def missing_partials(self):
        return {'location': '',
                'decorator': '',
                'purpose': '',
                'childtype': ''}


class TestNomenclateState(TestNomenclateBase):
    def test_state_clear(self):
        previous_state = self.nom.state
        self.nom.token_dict.reset()
        self.assertEquals(self.nom.state,
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.state = previous_state

    def test_state_valid(self):
        self.assertEquals({token: token_attr_dict['label'] for token, token_attr_dict in iteritems(self.nom.state)},
                          {'childtype': '',
                           'decorator': '',
                           'location': '',
                           'name': 'testObject',
                           'purpose': '',
                           'side': 'left',
                           'type': 'locator',
                           'var': 0})


class TestNomenclateResetFromConfig(TestNomenclateBase):
    def test_refresh(self):
        self.assertIsNone(self.nom.reset_from_config())


class TestNomenclateInitializeConfigSettings(TestNomenclateBase):
    pass


class TestNomenclateInitializeFormatOptions(TestNomenclateBase):
    def test_switch_naming_format_from_str(self):
        self.nom.initialize_format_options(self.test_format_b)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

        self.nom.initialize_format_options(self.test_format)
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose',
                                         'type']))

    def test_switch_multiple_naming_formats_from_config(self):
        self.nom.initialize_format_options(['naming_formats', 'riggers', 'lee_wolland'])
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['type', 'childtype', 'space', 'purpose', 'name', 'side']))

        self.nom.initialize_format_options(['naming_formats', 'riggers', 'raffaele_fragapane'])
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['name', 'height', 'Side', 'Depth', 'purpose']))

        self.nom.initialize_format_options(self.test_format)


class TestNomenclateSwapFormats(TestNomenclateBase):
    lee_path = ['naming_formats', 'riggers', 'lee_wolland']
    raf_path = ['naming_formats', 'riggers', 'raffaele_fragapane']

    def test_format_switch_same_format(self):
        nom = nm.Nom()
        nom_b = nm.Nom()
        self.assertEquals(nom.tokens, nom_b.tokens)
        nom.format = 'side_location_nameDecoratorVar_childtype_purpose_type'
        self.assertEquals(nom.tokens, nom_b.tokens)

    def test_format_switch_same_tokens(self):
        nom = nm.Nom()
        nom_b = nm.Nom()
        self.assertEquals(nom.tokens, nom_b.tokens)
        nom.format = 'type_purpose_name_childtype_decorator_var_location_side'
        self.assertEquals(nom.tokens, nom_b.tokens)

    def test_switch_multiple_naming_formats_use_initialize_format_options(self):
        self.nom.initialize_format_options(self.lee_path)
        self.set_values()
        self.assertEquals(self.nom.get(), 'LOC_hchy_test_l')
        self.nom.initialize_format_options(self.raf_path)
        self.set_raf_values()
        self.assertEquals(self.nom.get(), 'test_TLR_hchy')
        self.nom.initialize_format_options(self.test_format)

    def test_switch_multiple_naming_formats_set_format(self):
        self.nom.format = self.lee_path
        self.set_values()
        self.assertEquals(self.nom.get(), 'LOC_hchy_test_l')

        self.nom.format = self.raf_path
        self.set_raf_values()
        self.assertEquals(self.nom.get(), 'test_TLR_hchy')
        self.nom.initialize_format_options(self.test_format)

    def test_switch_single_format(self):
        self.nom.format = self.lee_path
        self.set_values()
        self.assertEquals(self.nom.get(), 'LOC_hchy_test_l')
        self.nom.format = self.raf_path
        self.set_raf_values()
        self.assertEquals(self.nom.get(), 'test_TLR_hchy')

    def test_switch_single_char_format(self):
        self.nom.format = 'a'
        self.nom.a = 'john'
        self.assertEquals(self.nom.get(), 'john')

    def test_switch_double_format(self):
        self.nom.format = 'af'
        self.nom.af = 'john'
        self.assertEquals(self.nom.get(), 'john')

    def test_switch_triple_format(self):
        self.nom.format = 'asd'
        self.nom.asd = 'john'
        self.assertEquals(self.nom.get(), 'john')

    def test_switch_single_format_nonsense(self):
        self.nom.format = 'asdf'
        self.nom.asdf = 'john'
        self.assertEquals(self.nom.get(), 'john')

    def test_switch_single_format_repeat(self):
        try:
            self.nom.format = 'asdf_asdf'
        except nm.core.errors.FormatError:
            pass

    def test_switch_single_format_repeat_different_casing(self):
        try:
            self.nom.format = 'asdf_Asdf'
        except nm.core.errors.FormatError:
            pass

    def set_values(self):
        self.nom.name = 'test'
        self.nom.height = 'top'
        self.nom.side = 'left'
        self.nom.depth = 'rear'
        self.nom.purpose = 'hierarchy'

    def set_raf_values(self):
        print('\n%r\n' % self.nom.height)
        self.nom.height = 'top'
        print('\n%r\n' % self.nom.height)
        self.nom.height.case = 'upper'
        self.nom.depth = 'rear'
        self.nom.depth.case = 'upper'
        self.nom.side.case = 'upper'


class TestNomenclateInitializeOptions(TestNomenclateBase):
    def test_options_stored(self):
        self.nom.CONFIG_OPTIONS = None
        self.nom.initialize_options()
        self.assertIsNotNone(self.nom.CONFIG_OPTIONS)


class TestNomenclateInitializeUiOptions(TestNomenclateBase):
    def test_pass_through(self):
        self.nom.initialize_ui_options()


class TestNomenclateMergeDict(TestNomenclateBase):
    def test_partial_merge(self):
        nom = nm.Nom()
        nom.merge_dict(self.partial_vars)
        _ = {}
        _.update(self.partial_vars)
        _.update(self.missing_partials)
        self.assertDictEqual({token: token_attr_dict['label'] for token, token_attr_dict in iteritems(nom.state)}, _)

    def test_not_Found_in_format_merge(self):
        nom = nm.Nom()
        random = {'weird': 'nope', 'not_here': 'haha', 'foo': 'bar'}
        nom.merge_dict(random)
        random.update(self.empty_vars)
        self.assertDictEqual(nom.state, random)


class TestNomenclateGetFormatOrderFromFormatString(TestNomenclateBase):
    def test_get_format_order(self):
        self.assertEquals(self.nom.format_string_object.parse_format_order(self.test_format),
                          ['side', 'location', 'name', 'Decorator', 'Var', 'childtype', 'purpose', 'type'])


class TestNomenclateGet(TestNomenclateBase):
    def test_get(self):
        self.assertEquals(self.nom.get(), 'l_testObjectA_LOC')

    def test_get_after_change(self):
        previous_state = self.nom.state
        self.nom.location.set('rear')
        self.assertEquals(self.nom.get(), 'l_rr_testObjectA_LOC')
        self.nom.state = previous_state


class TestNomenclateEq(TestNomenclateBase):
    def test_equal(self):
        other = nm.Nom(self.nom)
        self.assertTrue(other == self.nom)

    def test_inequal_one_diff(self):
        other = nm.Nom(self.nom.state)
        other.name = 'ronald'
        self.assertFalse(other == self.nom)

    def test_inequal_multi_diff(self):
        other = nm.Nom(self.nom.state)
        other.name = 'ronald'
        other.var = 'C'
        other.type = 'joint'
        print(other, '\n', self.nom)
        self.assertFalse(other == self.nom)


class TestNomenclateRepr(TestNomenclateBase):
    def test__str__(self):
        self.assertEquals(str(self.nom), 'l_testObjectA_LOC')


class TestNomenclateUnset(TestNomenclateBase):
    def test_non_full(self):
        nom = nm.Nom(self.partial_vars)

        _ = {}
        _.update(self.partial_vars)
        _.update(self.missing_partials)

        self.assertDictEqual({token: token_attr_dict['label'] for token, token_attr_dict in iteritems(nom.state)}, _)
        self.assertDictEqual(nom.empty_tokens, self.missing_partials)

    def test_create_empty(self):
        nom = nm.Nom()
        self.assertDictEqual(nom.state, self.empty_vars)
        self.assertDictEqual(nom.empty_tokens, self.empty_vars)

    def test_full(self):
        nom = nm.Nom(self.fill_vars)
        self.assertDictEqual({token: token_attr_dict['label'] for token, token_attr_dict in iteritems(nom.state)},
                             self.fill_vars)
        self.assertDictEqual(nom.empty_tokens, {})


class TestNomenclateTokens(TestNomenclateBase):
    def test_non_full(self):
        nom = nm.Nom()
        self.checkEqual(nom.tokens, list(self.empty_vars))

    def test_partial(self):
        nom = nm.Nom(self.partial_vars)
        self.checkEqual(nom.tokens, list(self.empty_vars))

    def test_full(self):
        nom = nm.Nom(self.fill_vars)
        self.checkEqual(nom.tokens, list(self.empty_vars))


class TestNomenclateDir(TestNomenclateBase):
    def test_default(self):
        nom = nm.Nom()
        for item in nom.tokens:
            self.assertIn(item.token, dir(nom))

    def test_merge_dict(self):
        nom = nm.Nom()
        random = {'weird': 'nope', 'not_here': 'haha', 'foo': 'bar'}
        nom.merge_dict(random)
        for item in list(random):
            self.assertIn(item, dir(nom))

    def test_swap_format(self):
        nom = nm.Nom()
        nom.format = ['naming_formats', 'riggers', 'raffaele_fragapane']
        for item in nom.tokens:
            self.assertIn(item.token, dir(nom))
