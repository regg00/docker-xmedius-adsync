import unittest
from libs.utils.utility import Utility


class TestUtility(unittest.TestCase):
    def test_strip_accents(self):
        self.assertEqual('e', Utility.strip_accents(u'\u00e9'))
        self.assertEqual('ecole', Utility.strip_accents(u'\u00e9cole'))

    def test_chinese_chars_not_stripped(self):
        self.assertEqual(u'\u4e2d', Utility.strip_accents(u'\u4e2d'))

    def test_verify_contains_key(self):
        self.assertFalse(Utility.verify_contain_keys({}, ['invalid']))
        self.assertFalse(Utility.verify_contain_keys({'valid': 'key'}, ['valid', 'invalid']))
        self.assertTrue(Utility.verify_contain_keys({'valid': 'key'}, ['valid']))
