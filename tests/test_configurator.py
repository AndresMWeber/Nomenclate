# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload
from future.utils import iteritems
import six

import mock
from pyfakefs import fake_filesystem
import nomenclate.core.configurator as config
import unittest
import mock
import collections
from pyfakefs import fake_filesystem
import nomenclate.core.configurator as config
from collections import OrderedDict


#@unittest.skip("skipping until finished testing nomenclate")
class TestNameparser(unittest.TestCase):

    def setUp(self):
        self.maxDiff=1000
        self.mock_config = MockConfig()
        self.cfg = self.mock_config.parser
        self.fixtures =[self.cfg, self.mock_config]

        # test values
        self.format_title = self.mock_config.format_title
        self.format_subcategory = self.mock_config.format_subcategory
        self.default_format = self.mock_config.default_format
        self.format_test = self.mock_config.format_test
        self.discipline_path = self.mock_config.discipline_path
        self.discipline_subsets = self.mock_config.discipline_subsets
        self.discipline_data = self.mock_config.discipline_data

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    @mock.patch('nomenclate.core.configurator.os.path.isfile')
    def test_valid_file_no_file(self, mock_isfile):
        mock_isfile.return_value = False
        self.assertRaises(IOError, self.cfg.validate_config_file, '/mock/config.yml')

    def test_get_as_string(self):
        self.assertEquals(self.cfg.get([self.format_title, self.default_format], return_type=str),
                          ' '.join(self.discipline_subsets))

    def test_get_options(self):
        self.assertTrue(self.checkEqual(self.cfg.get([self.format_title], return_type=list),
                                        ['texturing', 'node']))

    def test_query_valid_entry(self):
        self.cfg.validate_query_path(self.format_test)
        self.assertRaises(IndexError, self.cfg.validate_query_path, [self.format_title, 'submuerts'])
        self.assertRaises(IndexError, self.cfg.validate_query_path, ['faming_subsets', self.default_format])
        self.assertRaises(IndexError, self.cfg.validate_query_path, ['faming_subsets', 'dubsteps'])

    def test_get_section_ordered_dict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict),
                          OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x:x[0])))

    def test_get_section_ordered_dict_full_path(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict, preceding_depth=-1),
                          {'options':{'discipline': OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x:x[0]))}})

    def test_get_section_ordered_dict_partial_path(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict, preceding_depth=0),
                          {'discipline': OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x:x[0]))})

    def test_get_as_string(self):
        self.assertTrue(self.checkEqual(self.cfg.get(self.discipline_path, return_type=str).split(),
                                        self.discipline_subsets))

    def test_get_as_dict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=list, preceding_depth=-1),
                          {self.discipline_path[0]: {self.discipline_path[1]: self.discipline_subsets}})

    def test_get_as_dict_subdict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=dict),
                          self.discipline_data)

    def test_get(self):
        self.assertTrue(self.checkEqual(self.cfg.get(self.discipline_path, return_type=dict), self.discipline_subsets))

    def test_list_sections(self):
        print(self.cfg.get([], return_type=list))
        six.assertCountEqual(self,
                             self.cfg.get([], return_type=list),
                             ['overall_config', 'options', 'naming_formats'])

    def test_list_section_options(self):
        self.assertEquals(self.cfg.get(self.format_title, return_type=list),
                          ['node', 'texturing'])

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


class MockConfig():
    def __init__(self):
        self.build_test_config()

    @mock.patch('nomenclate.core.configurator.os.path.getsize')
    @mock.patch('nomenclate.core.configurator.os.path.isfile')
    @mock.patch('nomenclate.core.configurator.open', mock.mock_open(read_data=test_data))
    def build_test_config(self, mock_isfile, mock_getsize):
        mock_isfile.return_value = True
        mock_getsize.return_value = 700
        self.parser = config.ConfigParse()
        self.fakefs = fake_filesystem.FakeFilesystem()

        self.fake_file_path = '/var/env/foobar.yml'
        self.fake_file = self.fakefs.CreateFile(self.fake_file_path, contents=test_data)
        fake_filesystem.FakeFile(self.fakefs)
        self.parser.rebuild_config_cache(self.fake_file_path)

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