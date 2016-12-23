# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function

import nomenclate.core.nomenclature as nom
import unittest


class TestAcceptanceWorkflowBase(unittest.TestCase):
    def setUp(self):
        self.fixtures = []

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture


class TestCreation(TestAcceptanceWorkflowBase):
    def test_initialize_with_dict_only_one(self):
        n = nom.Nomenclate({'name': 'test'})
        n.new = 'default'
        self.assertEquals(n.get(), 'test')

    def test_initialize_with_dict_only_end_and_start(self):
        n = nom.Nomenclate({'side': 'left', 'type': 'locator'})
        n.new = 'default'
        self.assertEquals(n.get(), 'l_LOC')

    def test_initialize_with_dict_incomplete_and_swap_format(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        self.assertEquals(n.get(), 'l_default_testA_LOC')
        n.swap_format('new_nameDecoratorVar_childtype_purpose_type_side')
        n.new = 'default'
        self.assertEquals(n.get(), 'default_testA_LOC_l')
        self.fixtures.append(n)

    def test_initialize_with_dict_complete(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left', })
        n.new = 'default'
        self.assertEquals(n.get(), 'default_testA_LOC_l')

    def test_initialize_with_attributes_incomplete(self):
        pass

    def test_initialize_with_attributes_complete(self):
        pass

    def test_initialize_from_nomenclate_object(self):
        pass

    def test_initialize_from_nomenclate_state(self):
        pass

    def test_initialize_from_nomenclate_object_and_kwargs(self):
        pass

    def test_initialize_from_args(self):
        pass

    def test_initialize_and_switch_format_then_set_properties(self):
        n = nom.Nomenclate({'name': 'test', 'type': 'locator', 'var': 'A', 'side': 'left'})
        n.swap_format('new_nameDecoratorVar_childtype_purpose_type_side')
        n.new = 'default'
        self.assertEquals(n.get(), 'default_testA_LOC_l')

    def test_initialize_get_with_kwargs(self):
        pass


class TestAcceptanceMaya(TestAcceptanceWorkflowBase):
    pass


class TestAcceptanceSavingFiles(TestAcceptanceWorkflowBase):
    def test_saving_maya_file(self):
        pass

    def test_saving_movie_file(self):
        n = nom.Nomenclate()


class TestAcceptanceParsingExisting(TestAcceptanceWorkflowBase):
    def test_normal_maya_node(self):
        pass

    def test_working_file(self):
        pass

    def test_asset_file(self):
        pass

    def test_movie_file(self):
        pass
