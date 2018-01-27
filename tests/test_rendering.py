from six import iteritems
import nomenclate.core.rendering as rendering
import nomenclate.core.processing as processing
import nomenclate.core.errors as exceptions
import nomenclate.core.tokens as tokens
from tests.basetest import TestBase


class TestNomenclativeBase(TestBase):
    def setUp(self):
        super(TestNomenclativeBase, self).setUp()
        self.nomenclative_valid = processing.Nomenclative('side_location_nameDecoratorVar_childtype_purpose_type')
        self.nomenclative_valid_short = processing.Nomenclative('side_name_type')
        self.nomenclative_invalid = processing.Nomenclative('test_labelside')

        test_values = tokens.TokenAttrList(['side',
                                                   'location',
                                                   'name',
                                                   'decorator',
                                                   'var',
                                                   'childtype',
                                                   'purpose',
                                                   'type'])
        test_values['side'].set('left')
        test_values['location'].set('rear')
        test_values['name'].set('test')
        test_values['decorator'].set('')
        test_values['var'].set('A')
        test_values['childtype'].set('joints')
        test_values['purpose'].set('offset')
        test_values['type'].set('group')
        self.token_test_dict = test_values.to_json()

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
        test_dict = tokens.TokenAttrList(['name', 'side'])
        test_dict['name'].set('left')
        test_dict['side'].set('left')
        test_dict = test_dict.to_json()

        test_overlap = tokens.TokenAttrList(['side_name'])
        test_overlap['side_name'].set('overlapped')
        test_overlap = test_overlap.to_json()

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

