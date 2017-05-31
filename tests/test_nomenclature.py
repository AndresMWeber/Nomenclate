import unittest
import nomenclate.core.nomenclature as nm
import nomenclate.core.formatter as formatter
import nomenclate.core.configurator as config
import nomenclate.core.errors as exceptions
from . import basetest


class TestNomenclateBase(basetest.TestBase):
    def setUp(self):
        super(TestNomenclateBase, self).setUp()
        self.cfg = config.ConfigParse()
        self.test_format = 'side_location_nameDecoratorVar_childtype_purpose_type'
        self.test_format_b = 'location_nameDecoratorVar_childtype_purpose_type_side'

        self.nom = nm.Nomenclate()

        # Inject our fake config
        self.nom.cfg = self.cfg
        self.nom.side.set('left')
        self.nom.name.set('testObject')
        self.nom.type.set('locator')
        self.nom.var.set('A')
        self.fixtures = [self.cfg, self.nom, self.test_format_b, self.test_format]


class TestNomenclateTokens(TestNomenclateBase):
    pass


class TestNomenclateState(TestNomenclateBase):
    def test_state_clear(self):
        previous_state = self.nom.state
        self.nom.token_dict.reset()
        self.assertEquals(self.nom.state,
                          {'location': '', 'type': '', 'name': '', 'side': '', 'var': '', 'purpose': '',
                           'decorator': '', 'childtype': ''})
        self.nom.state = previous_state

    @unittest.skip
    def test_state_purge(self):
        previous_state = self.nom.state
        self.nom.token_dict.purge_name_attrs()
        self.assertEquals(self.nom.state, {})
        self.nom.state = previous_state

    def test_state_valid(self):
        self.assertEquals(self.nom.state,
                          {'childtype': '',
                           'decorator': '',
                           'location': '',
                           'name': 'testObject',
                           'purpose': '',
                           'side': 'left',
                           'type': 'locator',
                           'var': 'A'})


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
        self.nom.LOG.info(str(self.nom.format_order))
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['type', 'childtype', 'space', 'purpose', 'name', 'side']))

        self.nom.initialize_format_options(['naming_formats', 'riggers', 'raffaele_fragapane'])
        self.assertTrue(self.checkEqual(self.nom.format_order,
                                        ['name', 'height', 'Side', 'Depth', 'purpose']))

        self.nom.initialize_format_options(self.test_format)


class TestNomenclateSwapFormats(TestNomenclateBase):
    def test_switch_multiple_naming_formats_initialize_format_options(self):
        # TODO: Finalize and re-implement
        self.nom.initialize_format_options(['naming_formats', 'riggers', 'lee_wolland'])

        self.nom.LOG.info('New Format order: %s' % self.nom.format_order)
        self.nom.name = 'test'
        self.nom.side = 'left'
        self.nom.side_case = 'upper'
        self.nom.purpose = 'hierarchy'
        # self.assertEquals(self.nom.get(), 'LOC_hierarchy_test_l')

        self.nom.initialize_format_options(['naming_formats', 'riggers', 'raffaele_fragapane'])
        self.nom.height = 'top'
        self.nom.height_case = 'upper'
        self.nom.depth = 'rear'
        self.nom.depth_case = 'upper'

        # self.assertEquals(self.nom.get(), 'test_TLR_hierarchy')
        self.nom.LOG.info('%r' % self.nom.get())
        self.nom.LOG.info('New Format order: %s' % self.nom.format_order)

        self.nom.initialize_format_options(self.test_format)

    def test_switch_multiple_naming_formats_set_format(self):
        # TODO: Finalize and re-implement
        self.nom.format = ['naming_formats', 'riggers', 'lee_wolland']

        self.nom.LOG.info('New Format order: %s' % self.nom.format_order)
        self.nom.name = 'test'
        self.nom.height = 'top'
        self.nom.side = 'left'
        self.nom.depth = 'rear'
        self.nom.purpose = 'hierarchy'
        # self.assertEquals(self.nom.get(), 'LOC_hrc_test_l')

        self.nom.format = ['naming_formats', 'riggers', 'raffaele_fragapane']
        # self.assertEquals(self.nom.get(), 'test_TLR_hierarchy')
        self.nom.LOG.info('%r' % self.nom.get())
        self.nom.LOG.info('New Format order: %s' % self.nom.format_order)

        self.nom.initialize_format_options(self.test_format)


class TestNomenclateInitializeOptions(TestNomenclateBase):
    def test_options_stored(self):
        self.nom.CONFIG_OPTIONS = None
        self.nom.initialize_options()
        self.assertIsNotNone(self.nom.CONFIG_OPTIONS)


class TestNomenclateInitializeUiOptions(TestNomenclateBase):
    def test_pass_through(self):
        self.nom.initialize_ui_options()


class TestNomenclateMergeDict(TestNomenclateBase):
    pass


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


class TestNomenclateGetChain(TestNomenclateBase):
    def test_get_chain(self):
        self.assertRaises(NotImplementedError, self.nom.get_chain, (0, 5))
        # self.assertIsNone(self.nom.get_chain(0, 5))


class TestNomenclateUpdateTokenAttributes(TestNomenclateBase):
    pass


class TestNomenclateComposeName(TestNomenclateBase):
    pass


class TestNomenclateEq(TestNomenclateBase):
    def test_equal(self):
        other = nm.Nomenclate(self.nom)
        self.assertTrue(other == self.nom)

    def test_inequal_one_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        self.assertFalse(other == self.nom)

    def test_inequal_multi_diff(self):
        other = nm.Nomenclate(self.nom.state)
        other.name = 'ronald'
        other.var = 'C'
        other.type = 'joint'
        self.assertFalse(other == self.nom)


class TestNomenclateRepr(TestNomenclateBase):
    def test__str__(self):
        self.assertEquals(str(self.nom), 'l_testObjectA_LOC')

