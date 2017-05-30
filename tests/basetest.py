import unittest


class TestBase(unittest.TestCase):
    def setUp(self):
        self.fixtures = []
        print('running testBase setup!')

    def tearDown(self):
        for fixture in self.fixtures:
            del fixture

    @staticmethod
    def checkEqual(list_a, list_b):
        return len(list_a) == len(list_b) and sorted(list_a) == sorted(list_b)
