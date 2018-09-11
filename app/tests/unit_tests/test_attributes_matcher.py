import unittest
from libs.http.attributes_matcher import AttributesMatcher


class TestAttributesMatcher(unittest.TestCase):

    def test_no_config_data(self):
        config_data = {'attributes_mapping': {}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({}, matcher.match_attributes({}, {}))

    def test_config_data_no_attributes(self):
        config_data = {'attributes_mapping': {'portal_key1': 'ad_value1', 'portal_key2': 'ad_value2'}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({'portal_key1': '1', 'portal_key2': '2'},
                         matcher.match_attributes({'ad_value1': ['1'], 'ad_value2': ['2']}, {}))

    def test_config_data_with_attributes(self):
        config_data = {'attributes_mapping': {'portal_key1': 'ad_value1', 'portal_key2': 'ad_value2'}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({'portal_key1': '1', 'portal_key2': '2', 'portal_key3': '5'},
                         matcher.match_attributes({'ad_value1': ['1'], 'ad_value2': ['2']}, {'portal_key1': '3', 'portal_key2': '4', 'portal_key3': '5'}))

    def test_config_data_with_attribute_no_match_1(self):
        config_data = {'attributes_mapping': {}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({'portal_key3': '3', 'portal_key4': '4', 'portal_key5': '5'},
                         matcher.match_attributes({'ad_value1': ['1'], 'ad_value2': ['2']}, {'portal_key3': '3', 'portal_key4': '4', 'portal_key5': '5'}))

    def test_config_data_with_attribute_no_match_2(self):
        config_data = {'attributes_mapping': {'portal_key1': 'ad_value1', 'portal_key2': 'ad_value2'}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({'portal_key3': '3', 'portal_key4': '4', 'portal_key5': '5'},
                         matcher.match_attributes({}, {'portal_key3': '3', 'portal_key4': '4', 'portal_key5': '5'}))

    def test_can_extract_group_name_from_dn(self):
        config_data = {'attributes_mapping': {'portal_key1': 'ad_value1', 'portal_key2': 'ExtractGroupNameFromDN'}}
        matcher = AttributesMatcher(config_data, None, {}, None, {})
        self.assertEqual({'portal_key1': '1', 'portal_key2': 'group', 'portal_key3': '5'},
                         matcher.match_attributes({'distinguishedName': ['CN=user,OU=group'], 'ad_value1': ['1'], 'ad_value2': ['2']}, {'portal_key1': '3', 'portal_key2': '4', 'portal_key3': '5'}))
