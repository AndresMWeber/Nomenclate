# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import copy
import unittest
import mock
import configparser
from pyfakefs import fake_filesystem
import nomenclate.core.configurator as config
from collections import OrderedDict

reload(config)

__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"


class TestNameparser(unittest.TestCase):

    def setUp(self):
        self.fixture = config.ConfigParse()
        self.test_path = test_path = '/mock/config.ini'

        # Creating a fake filesystem for testing
        test_data = ('[naming_subsets]\nsubsets: modeling rigging texturing lighting utility\n[subset_formats]'
                     '\nmodeling: format_topGroup_model format_modelling format_subset format_geometry format_curve format_deformer'
                     '\n[suffix_pairs]\nformat_topGroup: group\n[suffixes]\nmesh : GEO\n[options]\nside: left right center'
                     '\nvar: A a #\n[naming_format]\nformat: {side}_{location}_{name}{decorator}{var}_{childType}_{purpose}_{type}\n')
        fakefs = fake_filesystem.FakeFilesystem()
        self.fake_file_path = '/var/env/foobar.ini'
        fakefs.CreateFile(self.fake_file_path, contents=test_data)
        fake_file = fake_filesystem.FakeFile(fakefs)
        self.fixture.load_config(self.fake_file_path)

        self.fixtures =[self.fixture, self.fake_file_path]

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    @mock.patch('nomenclate.core.configurator.os.path')
    def test_get_data_no_file(self, mock_path):
        mock_path.isfile.return_value = False
        self.assertRaises(IOError, self.fixture.load_config(self.test_path))

    @mock.patch('nomenclate.core.configurator.os.path')
    @mock.patch.object(configparser.ConfigParser, 'read')
    def test_get_data(self, mock_parser_read, mock_path):
        self.fixture.load_config(self.test_path)
        mock_path.isfile.return_value = True
        mock_parser_read.assert_called_with(self.test_path)

    def test_get(self):
        #section = None, subsection = None, options = False, raw = False
        self.assertEquals(self.fixture.get(section='naming_subsets', subsection='subsets'),
                          'modeling rigging texturing lighting utility')

    def test_get_options(self):
        #section = None, subsection = None, options = False, raw = False
        self.assertEquals(self.fixture.get(section='naming_subsets', options=True),
                          ['subsets'])

    def test_query_valid_entry(self):
        self.assertEquals(self.fixture.query_valid_entry('naming_subsets', 'subsets'), True)
        self.assertRaises(IOError, self.fixture.query_valid_entry, 'naming_subsets', 'submuerts',)
        self.assertRaises(IOError, self.fixture.query_valid_entry, 'faming_subsets', 'subsets',)
        self.assertRaises(IOError, self.fixture.query_valid_entry, 'faming_subsets', 'dubsteps',)

    def test_get_section(self):
        self.assertEquals(self.fixture.get_section(section='naming_subsets'),
                          OrderedDict([('subsets', 'modeling rigging texturing lighting utility')]))

    def test_get_section_raw(self):
        # TODO: Not sure if raw is working right...
        self.assertEquals(self.fixture.get_section(section='naming_subsets', raw=True),
                          OrderedDict([('subsets', 'modeling rigging texturing lighting utility')]))

    def test_get_subsection_as_dict(self):
        self.assertEquals(self.fixture.get_subsection_as_dict(section='naming_subsets', subsection='subsets'),
                          {'naming_subsets': {'subsets': ['modeling', 'rigging', 'texturing', 'lighting', 'utility']}})

    def test_get_subsection_as_list(self):
        self.assertEquals(self.fixture.get_subsection_as_list(section='naming_subsets', subsection='subsets'),
                          ['modeling', 'rigging', 'texturing', 'lighting', 'utility'])

    def test_get_subsection_as_str(self):
        self.assertEquals(self.fixture.get_subsection_as_str(section='naming_subsets', subsection='subsets'),
                          'modeling rigging texturing lighting utility')

    def test_get_sections(self):
        self.assertEquals(self.fixture.get_sections(),
                          ['naming_subsets', 'subset_formats', 'suffix_pairs', 'suffixes', 'options', 'naming_format'])

    def test_get_section_options(self):
        self.assertEquals(self.fixture.get_section_options('naming_subsets'),
                          ['subsets'])

    def test_deep_copy(self):
        self.assertIsInstance(copy.deepcopy(config.ConfigParse()).parser, configparser.ConfigParser)