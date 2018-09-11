import unittest
from libs.http.dn_extractor import DistinguishedNameExtractor
from libs.http.dn_extractor import DistinguishedNameExtractionException


class TestDistinguishedNameExtractor(unittest.TestCase):
    def test_extract_group_name(self):
        value = DistinguishedNameExtractor().extract_group_name('CN=username,OU=Users,DC=example,DC=com')
        self.assertEqual('Users', value)

    def test_extract_group_name_if_only_one_part(self):
        value = DistinguishedNameExtractor().extract_group_name('CN=username,OU=Users')
        self.assertEqual('Users', value)

    def test_raise_exception_if_extract_group_name_has_nothing_interesting_to_extract(self):
        try:
            DistinguishedNameExtractor().extract_group_name('OU')
            self.fail()
        except DistinguishedNameExtractionException:
            pass

    def test_raise_exception_if_extract_group_name_has_nothing_to_extract(self):
        try:
            DistinguishedNameExtractor().extract_group_name('')
            self.fail()
        except DistinguishedNameExtractionException:
            pass
