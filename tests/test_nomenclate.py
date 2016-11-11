# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function
from imp import reload

import unittest
import nomenclate.core.nomenclature as nm
reload(nm)


class TestNomenclate(unittest.TestCase):
    def setUp(self):
        self.fixture = nm.Nomenclate()

    def tearDown(self):
        del self.fixture

    def format_options(self):
        self.assertEqual(self.fixture.format_options, None)

    def test(self):
       self.failUnlessEqual(range(1, 10), range(1, 10))