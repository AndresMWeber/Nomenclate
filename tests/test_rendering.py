from six import iteritems
import nomenclate.core.rendering as rendering
import nomenclate.core.processing as processing
import nomenclate.core.errors as exceptions
from . import basetest


class TestNomenclativeBase(basetest.TestBase):
    def setUp(self):
        super(TestNomenclativeBase, self).setUp()
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


class TestNomenclativeProcessMatches(TestNomenclativeBase):
    def test_valid(self):
        test_dict = self.token_test_dict.copy()
        rendering.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid.raw_formatted_string)
        for token, value in iteritems(test_dict):
            self.nomenclative_valid.add_match(*value)
        self.assertEquals(self.nomenclative_valid.process_matches(),
                          'left_rear_testA_joints_offset_group')

    def test_valid_short(self):
        test_dict = self.token_test_dict.copy()
        rendering.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid_short.raw_formatted_string)
        for token, value in iteritems(test_dict):
            if isinstance(value, str):
                pass
            else:
                self.nomenclative_valid_short.add_match(*value)
        self.assertEquals(self.nomenclative_valid_short.process_matches(),
                          'left_test_group')

    def test_invalid(self):
        self.assertEquals(self.nomenclative_invalid.process_matches(),
                          self.nomenclative_invalid.raw_formatted_string)


class TestNomenclativeAddMatch(TestNomenclativeBase):
    def test_valid(self):
        test_dict = self.token_test_dict.copy()
        rendering.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid.raw_formatted_string)
        for token, value in iteritems(test_dict):
            self.nomenclative_valid.add_match(*value)
        self.assertEquals(self.nomenclative_valid.process_matches(),
                          'left_rear_testA_joints_offset_group')

    def test_short_valid(self):
        test_dict = self.token_test_dict.copy()
        rendering.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid_short.raw_formatted_string)
        for token, value in iteritems(test_dict):
            if not isinstance(value, str):
                self.nomenclative_valid_short.add_match(*value)
        self.assertEquals(self.nomenclative_valid_short.process_matches(),
                          'left_test_group')

    def test_overlap(self):
        test_dict = {'name': 'left', 'side': 'left'}
        test_overlap = {'side_name': 'overlapped'}
        rendering.InputRenderer._prepend_token_match_objects(test_dict, self.nomenclative_valid_short.raw_formatted_string)
        rendering.InputRenderer._prepend_token_match_objects(test_overlap, self.nomenclative_valid_short.raw_formatted_string)

        for token, value in iteritems(test_dict):
            if not isinstance(value, str):
                self.nomenclative_valid_short.add_match(*value)

        for token, value in iteritems(test_overlap):
            if not isinstance(value, str):
                self.assertRaises(exceptions.OverlapError, self.nomenclative_valid_short.add_match, *value)

    def test_non_regex_match_object(self):
        self.assertEquals(self.nomenclative_invalid.process_matches(),
                          self.nomenclative_invalid.raw_formatted_string)

