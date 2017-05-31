import nomenclate.core.nomenclature as nom
from . import basetest


class TestCreation(basetest.TestBase):
    def test_initialize_with_dict_only_one(self):
        n = nom.Nomenclate({'name': 'test'})
        n.new = 'default'
        self.assertEquals(n.get(), 'test')

    def test_initialize_with_dict_only_end_and_start(self):
        n = nom.Nomenclate({'side': 'left', 'type': 'locator'})
        n.new = 'default'
        self.assertEquals(n.get(), 'l_LOC')

    def test_initialize_with_dict_incomplete_and_swap_format_from_new_string(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        self.assertEquals(n.get(), 'l_testA_LOC')
        n.format = 'new_nameDecoratorVar_childtype_purpose_type_side'
        n.new = 'default'
        self.assertEquals(n.get(), 'default_testA_LOC_l')
        self.fixtures.append(n)

    def test_initialize_with_dict_incomplete_and_swap_format_from_path(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        self.assertEquals(n.get(), 'l_testA_LOC')
        n.format = ['naming_formats', 'node', 'format_archive']
        self.assertEquals(n.get(), 'l_test_LOC')
        self.fixtures.append(n)

    def test_initialize_with_dict_complete(self):
        n = nom.Nomenclate({'name': 'test',
                            'decorator': 'J',
                            'childtype': 'joint',
                            'purpose': 'offset',
                            'var': 'A',
                            'side': 'left',
                            'type': 'locator',
                            'location': 'rear'})
        self.assertEquals(n.get(), 'l_rr_testJA_joint_offset_LOC')

    def test_initialize_with_attributes_incomplete(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        self.assertEquals(n.get(), 'l_testA_LOC')
        self.fixtures.append(n)

    def test_initialize_with_attributes_complete(self):
        n = nom.Nomenclate()
        n.name = 'test'
        n.decorator = 'J'
        n.childtype = 'joint'
        n.purpose = 'offset'
        n.var = 'A'
        n.side = 'left'
        n.type = 'locator'
        n.location = 'rear'
        n.LOG.info(str(n.state))
        self.assertEquals(n.get(), 'l_rr_testJA_joint_offset_LOC')
        self.fixtures.append(n)

    def test_initialize_from_nomenclate_object(self):
        n_initial = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        n_secondary = nom.Nomenclate(n_initial)
        self.assertEquals(n_secondary.get(), 'l_testA_LOC')
        self.fixtures.extend([n_secondary, n_initial])

    def test_initialize_from_nomenclate_state(self):
        n_initial = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        state_dict = n_initial.state
        n_secondary = nom.Nomenclate(state_dict)
        self.assertEquals(n_secondary.get(), 'l_testA_LOC')
        self.fixtures.extend([n_secondary, n_initial, state_dict])

    def test_initialize_from_nomenclate_object_and_kwargs(self):
        n_initial = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        n_secondary = nom.Nomenclate(n_initial, **{'name': 'blah', 'location': 'rear'})
        self.assertEquals(n_secondary.get(), 'l_rr_blahA_LOC')
        self.fixtures.extend([n_secondary, n_initial])

    def test_initialize_from_nomenclate_and_kwargs(self):
        n_initial = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        n_secondary = nom.Nomenclate(n_initial, name='blah', location='rear')
        self.assertEquals(n_secondary.get(), 'l_rr_blahA_LOC')
        self.fixtures.extend([n_secondary, n_initial])

    def test_initialize_and_switch_format_then_set_properties(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        n.initialize_format_options('new_nameDecoratorVar_childtype_purpose_type_side')
        n.name = 'default'
        self.assertEquals(n.get(), 'defaultA_LOC_l')

    def test_initialize_with_nomenclate_and_get_kwargs(self):
        n_initial = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        n_secondary = nom.Nomenclate(n_initial)
        self.assertEquals(n_secondary.get(name='blah', location='rear'), 'l_rr_blahA_LOC')
        self.fixtures.extend([n_secondary, n_initial])


class TestAcceptanceMaya(basetest.TestBase):
    pass


class TestAcceptanceNamingFiletypes(basetest.TestBase):
    def test_saving_maya_file(self):
        n = nom.Nomenclate(name='SH010', var='A', ext='mb', initials='aw', discipline='animation', version=5)
        n.initialize_format_options('working_file')
        self.assertEquals(n.format, 'name_discipline_lodDecoratorVar_version_initials.ext')
        self.assertEquals(n.get(), 'SH010_ANIM_A_v005_aw.mb')
        self.fixtures.append(n)

    def test_saving_movie_file(self):
        n = nom.Nomenclate()
        n.initialize_format_options('techops_file')
        n.merge_dict({'shot': 'LSC_sh01',
                      'version': 8,
                      'name': 'Nesquick',
                      'type': 'SFX_MS',
                      'status': 'WIP',
                      'date': 'September 21, 2005',
                      'filetype': 'Quicktime',
                      'var': 'A',
                      'ext': 'mov',
                      'initials': 'aw',
                      'discipline': 'animation',
                      'quality': '540p',
                      'version1': 3,
                      'version_padding': 1,
                      'version1_format': 'v#',
                      'version1_padding': 1})
        self.assertEquals('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_2005-09-21-540p_Quicktime.mov', n.get())
        n.date_format = '%m%d%y'
        self.assertEquals('LSC_sh01_v8_Nesquick_SFX_MS_WIP_v3_092105-540p_Quicktime.mov', n.get())

        self.fixtures.append(n)


class TestAcceptanceParsingExisting(basetest.TestBase):
    def test_normal_maya_node(self):
        pass

    def test_working_file(self):
        pass

    def test_asset_file(self):
        pass

    def test_movie_file(self):
        pass
