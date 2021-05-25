import unittest
from collections import Iterable


class TestBase(unittest.TestCase):
    def setUp(self):
        super(TestBase, self).setUp()
        self.fixtures = []

    def tearDown(self):
        super(TestBase, self).tearDown()
        for fixture in self.fixtures:
            del fixture

    @staticmethod
    def checkEqual(list_a, list_b):
        return len(list_a) == len(list_b) and sorted(list_a) == sorted(list_b)

    def assertDictEqual(self, d1, d2, msg=None):  # assertEqual uses for dicts
        for k, v1 in d1.items():
            self.assertIn(k, d2, msg)
            v2 = d2[k]
            if isinstance(v1, Iterable) and not isinstance(v1, str):
                self.checkEqual(v1, v2)
            else:
                self.assertEqual(v1, v2, msg)
        return True
