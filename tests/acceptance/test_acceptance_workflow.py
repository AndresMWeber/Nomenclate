# Ensure Python 2/3 compatibility: http://python-future.org/compatible_idioms.html
from __future__ import print_function

import unittest


class TestAcceptanceWorkflowBase(unittest.TestCase):
    def setUp(self):
        self.fixtures = []

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture
