#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import unittest
from mock import patch, Mock, MagicMock
from libs.ldap.ldap_wrapper import LDAPWrapper
import ldap
import base64


@patch.object(LDAPWrapper, 'connect_to_ldap_server', Mock())
def build_ldap_mock():
    base64.b16encode = MagicMock(return_value=[123])
    return LDAPWrapper(None, None)


class TestLdapPageSearch(unittest.TestCase):

    @patch('ldap.ldapobject.LDAPObject')
    def setUp(self, ldap_object_mock):
        self.ldap_mock = build_ldap_mock()
        self.ldap_mock._server_handler = ldap_object_mock
        self.ldap_mock._server_handler.search_ext = MagicMock(return_value=None)

    def test_no_results(self):
        self.ldap_mock._server_handler.result3 = MagicMock(return_value=(None, None, None, None))
        self.assertEqual([], self.ldap_mock._ldap_page_search("", "", "", []))

    def test_with_single_result_and_wrong_search_type(self):
        self.ldap_mock._server_handler.result3 = MagicMock(return_value=(None, "DATA", None, []))
        self.assertEqual([], self.ldap_mock._ldap_page_search("", "", "", []))

    def test_with_single_result_and_ok_search_type(self):
        self.ldap_mock._server_handler.result3 = MagicMock(return_value=(ldap.RES_SEARCH_RESULT, ["DATA"], None, []))
        self.assertEqual(['DATA'], self.ldap_mock._ldap_page_search("", "", "", []))


class TestFormatLdapFilter(unittest.TestCase):

    def setUp(self):
        self.ldap_mock = build_ldap_mock()

    def test_no_parameters(self):
        self.assertEqual("(&())", self.ldap_mock._format_ldap_filter("", []))

    def test_without_additional_filters_and_without_parentheses(self):
        self.assertEqual("(&(Test))", self.ldap_mock._format_ldap_filter("Test", []))

    def test_without_additional_filters_and_with_parentheses(self):
        self.assertEqual("(&(Test))", self.ldap_mock._format_ldap_filter("(Test)", []))

    def test_with_additional_filters(self):
        self.assertEqual("(&(Test)(1)(2)(3))", self.ldap_mock._format_ldap_filter("Test", ["1", "2", "3"]))

    def test_with_only_additional_filters(self):
        self.assertEqual("(&()(1)(2)(3))", self.ldap_mock._format_ldap_filter("", ["1", "2", "3"]))


class TestFindEntriesByUsn(unittest.TestCase):

    def setUp(self):
        self.ldap_mock = build_ldap_mock()
        self.ldap_mock._format_ldap_filter = MagicMock(return_value=[])

    def test_no_parameters(self):
        self.assertEqual({}, self.ldap_mock._find_entries_by_usn(0, 0, [], []))

    def test_incomplete_entry(self):
        self.assertRaises(Exception, self.ldap_mock._find_entries_by_usn, 0, 0, [[]], [])

    def test_no_results(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[])
        self.assertEqual({}, self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': []}], []))

    def test_with_results(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[('TEST', {'uSNChanged': ['Test'], 'objectGUID': [123]})])
        self.assertEqual({0: [{'usn_changed': 'Test', 'ad_data': {'objectGUID': [[123]], 'uSNChanged': ['Test']}}]},
                         self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': []}], []))

    def test_with_exclusion(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[('TEST', {'uSNChanged': ['Test'], 'objectGUID': [123], 'mail': ["hello@example.com"]})])
        output = self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': [], 'exclusion': {'mail': ["hello*"]}}], [])
        self.assertEqual({}, output)

    def test_with_exclusion_as_second_param(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[('TEST', {'uSNChanged': ['Test'], 'objectGUID': [123], 'mail': ["hello@example.com"]})])
        output = self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': [], 'exclusion': {'mail': ["no-match*", "hello*"]}}], [])
        self.assertEqual({}, output)

    def test_with_exclusion_of_attribute_list(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[('TEST', {'uSNChanged': ['Test'], 'objectGUID': [123], 'mail': ["no-match", "hello@example.com"]})])
        output = self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': [], 'exclusion': {'mail': ["hello*"]}}], [])
        self.assertEqual({}, output)

    def test_with_exclusion_of_any_attribute(self):
        self.ldap_mock._ldap_page_search = MagicMock(return_value=[('TEST', {'uSNChanged': ['Test'], 'objectGUID': [123], 'some-attribute': ["hello"]})])
        output = self.ldap_mock._find_entries_by_usn(0, 0, [{'base': 0, 'scope': 1, 'filter': [], 'exclusion': {'some-attribute': ["hello*"]}}], [])
        self.assertEqual({}, output)


class TestGetHighestUsnComitted(unittest.TestCase):

    @patch('ldap.ldapobject.LDAPObject')
    def setUp(self, ldap_object_mock):
        self.ldap_mock = build_ldap_mock()
        self.ldap_mock._server_handler = ldap_object_mock

    def test_fail(self):
        self.ldap_mock._server_handler.search = MagicMock(return_value=Exception())
        self.assertRaises(Exception, self.ldap_mock.get_highest_usn_comitted)

    def test_with_result(self):
        self.ldap_mock._server_handler.search = MagicMock(return_value=None)
        self.ldap_mock._server_handler.result = MagicMock(return_value=(ldap.RES_SEARCH_ENTRY, [[0, {'highestCommittedUSN': [10]}]]))
        self.assertEqual(10, self.ldap_mock.get_highest_usn_comitted())


class TestConnectToLdapServer(unittest.TestCase):

    @patch('ldap.ldapobject.LDAPObject')
    def setUp(self, ldap_object_mock):
        self.ldap_mock = build_ldap_mock()
        self.ldap_mock._server_handler = ldap_object_mock

    @patch.object(ldap, 'initialize')
    def test_no_fail(self, mocked_initialize):
        self.ldap_mock._server_handler.simple_bind_s = None
        self.assertEqual(None, self.ldap_mock.connect_to_ldap_server({'address': '', 'port': 0, 'username': '', 'password': ''}))

    @patch.object(ldap, 'initialize', Mock(return_value=Exception()))
    def test_fail(self):
        self.assertRaises(Exception, self.ldap_mock.connect_to_ldap_server, None)
