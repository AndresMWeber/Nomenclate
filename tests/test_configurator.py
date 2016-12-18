# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload
import six

import unittest
import mock
import collections
from pprint import pprint
from pyfakefs import fake_filesystem
import nomenclate.core.configurator as config
from collections import OrderedDict

reload(config)

__author__ = "Andres Weber"
__email__ = "andresmweber@gmail.com"

test_data = ('overall_config:\n'
             '  version_padding: 3\n'
             'naming_formats:\n'
             '  node:\n'
             '    default: side_location_nameDecoratorVar_childtype_purpose_type\n'
             '    format_archive: side_name_space_purpose_decorator_childtype_type\n'
             '    format_lee: type_childtype_space_purpose_name_side\n'
             '  texturing:\n'
             '    shader: side_name_type\n'
             'options:\n'
             '  discipline:\n'
             '    animation: AN ANI ANIM ANIMN\n'
             '    lighting: LT LGT LGHT LIGHT\n'
             '    rigging: RG RIG RIGG RIGNG\n'
             '    matchmove: MM MMV MMOV MMOVE\n'
             '    compositing: CM CMP COMP COMPG\n'
             '    modeling: MD MOD MODL MODEL\n'
             '  side:\n'
             '    - left\n'
             '    - right\n'
             '    - center\n')

#@unittest.skip("skipping until finished testing nomenclate")
class TestNameparser(unittest.TestCase):

    @mock.patch('nomenclate.core.configurator.os.path.isfile')
    @mock.patch('nomenclate.core.configurator.open', mock.mock_open(read_data=test_data))
    def setUp(self, mock_isfile):
        self.maxDiff=1000
        mock_isfile.return_value=True
        self.fixture = config.ConfigParse()
        # Creating a fake filesystem for testing
        self.fakefs = fake_filesystem.FakeFilesystem()

        self.fake_file_path = '/var/env/foobar.yml'
        self.fake_file = self.fakefs.CreateFile(self.fake_file_path, contents=test_data)
        fake_filesystem.FakeFile(self.fakefs)
        self.fixture.rebuild_config_cache(self.fake_file_path)
        self.fixtures =[self.fixture, self.fake_file_path, self.fake_file, self.fakefs]

        # test values
        self.format_title = 'naming_formats'
        self.format_subcategory = 'node'
        self.default_format = 'default'
        self.format_test = [self.format_title, self.format_subcategory, self.default_format]
        self.discipline_path = ['options', 'discipline']
        self.discipline_subsets = ['animation', 'modeling', 'rigging', 'compositing', 'matchmove', 'lighting']
        self.discipline_data = {'animation': 'AN ANI ANIM ANIMN',
                                'compositing': 'CM CMP COMP COMPG',
                                'lighting': 'LT LGT LGHT LIGHT',
                                'matchmove': 'MM MMV MMOV MMOVE',
                                'modeling': 'MD MOD MODL MODEL',
                                'rigging': 'RG RIG RIGG RIGNG'}

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    @mock.patch('nomenclate.core.configurator.os.path.isfile')
    def test_valid_file_no_file(self, mock_isfile):
        mock_isfile.return_value = False
        self.assertRaises(IOError, self.fixture.validate_config_file, '/mock/config.yml')

    def test_get_as_string(self):
        self.assertEquals(self.fixture.get([self.format_title, self.default_format], return_type=str),
                          ' '.join(self.discipline_subsets))

    def test_get_options(self):
        self.assertTrue(self.checkEqual(self.fixture.get([self.format_title], return_type=list),
                                        ['texturing', 'node']))

    def test_query_valid_entry(self):
        self.assertEquals(self.fixture.validate_query_path([self.format_test]),
                          True)
        self.assertRaises(IndexError, self.fixture.validate_query_path, [self.format_title, 'submuerts'])
        self.assertRaises(IndexError, self.fixture.validate_query_path, ['faming_subsets', self.default_format])
        self.assertRaises(IndexError, self.fixture.validate_query_path, ['faming_subsets', 'dubsteps'])

    def test_get_section_ordered_dict(self):
        self.assertEquals(self.fixture.get(self.discipline_path, return_type=OrderedDict),
                          OrderedDict([(self.discipline_path[0], {self.discipline_path[1]: self.discipline_subsets})]))

    def test_get_section_ordered_dict_sub_dict(self):
        self.assertEquals(self.fixture.get(self.discipline_path, return_type=OrderedDict, preceding_depth=1),
                          OrderedDict([(self.default_format, ' '.join(self.discipline_subsets))]))

    def test_get_as_string(self):
        self.assertTrue(self.checkEqual(self.fixture.get(self.discipline_path, return_type=str).split(),
                                        self.discipline_subsets))

    def test_get_as_dict(self):
        self.assertEquals(self.fixture.get(self.discipline_path, return_type=list, preceding_depth=-1),
                          {self.discipline_path[0]: {self.discipline_path[1]: self.discipline_subsets}})

    def test_get_as_dict_subdict(self):
        self.assertEquals(self.fixture.get(self.discipline_path),
                          self.discipline_data)

    def test_get(self):
        self.assertTrue(self.checkEqual(self.fixture.get(self.discipline_path, return_type=dict), self.discipline_subsets))

    def test_list_sections(self):
        six.assertCountEqual(self,
                             self.fixture.get([], return_type=list),
                             [self.format_title, 'subset_formats', 'suffix_pairs', 'suffixes', 'options', 'naming_format'])

    def test_list_section_options(self):
        self.assertEquals(self.fixture.list_section_options(self.format_title),
                          [self.default_format])

    @staticmethod
    def checkEqual(L1, L2):
        return len(L1) == len(L2) and sorted(L1) == sorted(L2)

    def assertDictEqual(self, d1, d2, msg=None):  # assertEqual uses for dicts
        for k, v1 in d1.iteritems():
            self.assertIn(k, d2, msg)
            v2 = d2[k]
            if (isinstance(v1, collections.Iterable) and
                    not isinstance(v1, basestring)):
                self.checkEqual(v1, v2)
            else:
                self.assertEqual(v1, v2, msg)
        return True