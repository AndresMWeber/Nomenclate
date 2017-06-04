from six import iteritems, assertCountEqual
import mock
import os
import json
from tempfile import mkstemp
from pyfakefs import fake_filesystem
from collections import OrderedDict
from os.path import expanduser

import nomenclate.core.configurator as config
import nomenclate.core.errors as exceptions
from . import basetest


class TestConfiguratorBase(basetest.TestBase):
    def setUp(self):
        super(TestConfiguratorBase, self).setUp()
        self.maxDiff = 1000
        self.mock_config = MockConfig()
        self.cfg = self.mock_config.parser
        self.fixtures = [self.cfg, self.mock_config]

        # test values
        self.format_title = self.mock_config.format_title
        self.format_subcategory = self.mock_config.format_subcategory
        self.default_format = self.mock_config.default_format
        self.format_test = self.mock_config.format_test
        self.discipline_path = self.mock_config.discipline_path
        self.discipline_subsets = self.mock_config.discipline_subsets
        self.discipline_data = self.mock_config.discipline_data


class TestValidateConfigFile(TestConfiguratorBase):
    @mock.patch('nomenclate.core.configurator.os.path.isfile')
    def test_valid_file_no_file(self, mock_isfile):
        mock_isfile.return_value = False
        self.assertRaises(IOError, self.cfg.validate_config_file, '/mock/config.yml')


class TestGet(TestConfiguratorBase):
    def test_get_default_as_string(self):
        self.assertEquals(self.cfg.get([self.format_title, 'node', self.default_format], return_type=str),
                          'side_location_nameDecoratorVar_childtype_purpose_type')

    def test_get_options(self):
        self.assertTrue(self.checkEqual(self.cfg.get([self.format_title], return_type=list),
                                        ['texturing', 'node']))

    def test_query_valid_entry(self):
        self.cfg.get(self.format_test)
        self.assertRaises(exceptions.ResourceNotFoundError, self.cfg.get, [self.format_title, 'submuerts'])
        self.assertRaises(exceptions.ResourceNotFoundError, self.cfg.get, ['faming_subsets', self.default_format])
        self.assertRaises(exceptions.ResourceNotFoundError, self.cfg.get, ['faming_subsets', 'dubsteps'])

    def test_get_section_ordered_dict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict),
                          OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x: x[0])))

    def test_get_section_ordered_dict_full_path(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict, preceding_depth=-1),
                          {'options': {
                              'discipline': OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x: x[0]))}})

    def test_get_section_ordered_dict_partial_path(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=OrderedDict, preceding_depth=0),
                          {'discipline': OrderedDict(sorted(iteritems(self.discipline_data), key=lambda x: x[0]))})

    def test_get_disciplines_as_string(self):
        self.assertTrue(self.checkEqual(self.cfg.get(self.discipline_path, return_type=str).split(),
                                        self.discipline_subsets))

    def test_get_as_string_search(self):
        self.assertTrue(self.checkEqual(self.cfg.get('animation', return_type=str),
                                        'AN ANI ANIM ANIMN'))

    def test_get_as_dict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=list, preceding_depth=-1),
                          {self.discipline_path[0]: {self.discipline_path[1]: self.discipline_subsets}})

    def test_get_as_dict_subdict(self):
        self.assertEquals(self.cfg.get(self.discipline_path, return_type=dict),
                          self.discipline_data)

    def test_get(self):
        self.assertTrue(self.checkEqual(self.cfg.get(self.discipline_path, return_type=dict), self.discipline_subsets))

    def test_list_sections(self):
        assertCountEqual(self,
                         self.cfg.get([], return_type=list),
                         ['overall_config', 'options', 'naming_formats'])

    def test_list_section_options(self):
        self.assertEquals(self.cfg.get(self.format_title, return_type=list),
                          ['node', 'texturing'])

    def test_default_get(self):
        self.assertEquals(self.cfg.get(return_type=str),
                          "")

    def test_default_get_no_return_type(self):
        self.assertEquals(self.cfg.get(),
                          ['overall_config', 'options', 'naming_formats'])


class TestGetDefaultConfigFile(TestConfiguratorBase):
    def test_existing(self):
        config.ConfigParse()

    def test_custom(self):
        fd, temp_path = mkstemp()
        f = open(temp_path, 'w')
        f.write(json.dumps({'name': 'john', 'location': 'top'}))
        f.close()
        custom_config = config.ConfigParse(temp_path)
        self.assertDictEqual(custom_config.config_file_contents, OrderedDict([('name', 'john'), ('location', 'top')]))
        os.close(fd)
        os.remove(temp_path)

    def test_custom_empty(self):
        fd, temp_path = mkstemp()
        self.assertRaises(IOError, config.ConfigParse.validate_config_file, temp_path)
        os.close(fd)
        os.remove(temp_path)

    def test_custom_no_yaml_data(self):
        fd, temp_path = mkstemp()
        f = open(temp_path, 'w')
        f.write('#Empty YAML File')
        f.close()
        self.assertRaises(IOError, config.ConfigParse.validate_config_file, temp_path)
        os.close(fd)
        os.remove(temp_path)

    @mock.patch('nomenclate.core.configurator.ConfigParse.validate_config_file')
    def test_no_valid_config_file(self, mock_validate_config_file):
        mock_validate_config_file.side_effect = IOError('mock: config file not found')
        self.assertRaises(exceptions.SourceError, config.ConfigParse)


class TestGetHandler(TestConfiguratorBase):
    def test_existing(self):
        config.ConfigEntryFormatter.get_handler(str, list)

    def test_not_existing(self):
        self.assertRaises(IndexError, config.ConfigEntryFormatter.get_handler, int, str)


class MockConfig(object):
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
        self.fake_file = self.fakefs.CreateFile(self.fake_file_path, contents=self.test_data)
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


class TestFormatters(TestConfiguratorBase):
    def test_base_formatter_init(self):
        self.assertRaises(NotImplementedError, config.BaseFormatter.format_result, '')

    def test_dict_to_ordered_dict(self):
        self.assertEquals(config.DictToOrderedDict.format_result({}),
                          OrderedDict())

    def test_none_to_dict(self):
        self.assertEquals(config.NoneToDict.format_result(None),
                          {})

    def test_int_to_list(self):
        self.assertEquals(config.IntToList.format_result(1),
                          [1])

    def test_list_to_str(self):
        self.assertEquals(config.ListToString.format_result(['john', 'kate']),
                          'john kate')
