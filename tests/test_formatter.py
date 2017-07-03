import nomenclate.core.formatter as formatter
import nomenclate.core.errors as exceptions
from . import basetest


class TestFormatStringBase(basetest.TestBase):
    def setUp(self):
        super(TestFormatStringBase, self).setUp()
        self.fs = formatter.FormatString()
        self.fixtures.append(self.fs)


class TestFormatStringValidateFormatString(TestFormatStringBase):
    def test_get__validate_format_string_valid(self):
        self.fs.get_valid_format_order('side_mide')

    def test_get__validate_format_string__is_format_invalid(self):
        self.assertRaises(exceptions.FormatError, self.fs.get_valid_format_order, 'notside;blah')
