#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////


import unittest
from mock import patch, Mock, MagicMock
from adsync import ADSync
from libs.utils.utility import Utility


@patch.object(ADSync, '_load_ressources', Mock())
@patch.object(ADSync, 'run', Mock())
def build_ad_mock():
    Utility.parse_yaml = MagicMock()
    return ADSync()


class TestInit(unittest.TestCase):

    def setUp(self):
        self.adsync_mock = build_ad_mock()

    def test_instance_created(self):
        self.assertEqual(True, isinstance(self.adsync_mock, ADSync))


class TestLoadRessources(unittest.TestCase):

    def setUp(self):
        self.adsync_mock = build_ad_mock()

    def test_no_fail(self):
        self.adsync_mock._load_config = MagicMock()
        self.adsync_mock._load_modules = MagicMock()
        self.adsync_mock._load_ressources()


class TestLoadConfig(unittest.TestCase):

    def setUp(self):
        self.adsync_mock = build_ad_mock()

    def test_default_file(self):
        self.adsync_mock._load_config([])

    def test_wrong_command_arg(self):
        self.adsync_mock._load_config(['does_not_exist.yaml'])

    def test_test_file(self):
        self.adsync_mock._load_config(['test.yaml'])


class TestCreateSyncList(unittest.TestCase):

    @patch('libs.user_repository.UserRepository')
    def setUp(self, user_repo_mock):
        self.adsync_mock = build_ad_mock()
        self.adsync_mock._user_repository = user_repo_mock

    def test_empty_list(self):
        self.assertEqual([], self.adsync_mock._create_sync_list({}, {}))

    def test_add(self):
        self.adsync_mock._user_repository.check_user_exist.return_value = False
        result = self.adsync_mock._create_sync_list({'test': [{'ad_data': {'objectGUID': '123', 'userAccountControl': enabled_user_account_control()}}]}, {})[0]
        self.assertEqual({'objectGUID': '123', 'userAccountControl': enabled_user_account_control()}, result['ad_data'])
        self.assertEqual('Add user', result['description'])

    def test_update(self):
        self.adsync_mock._user_repository.check_user_exist.return_value = True
        result = self.adsync_mock._create_sync_list({'test': [{'ad_data': {'objectGUID': '123', 'userAccountControl': enabled_user_account_control()}}]}, {})[0]
        self.assertEqual({'objectGUID': '123', 'userAccountControl': enabled_user_account_control()}, result['ad_data'])
        self.assertEqual('Update user', result['description'])

    def test_remove(self):
        result = self.adsync_mock._create_sync_list({}, {'test': [{'ad_data': {'objectGUID': '123'}}]})[0]
        self.assertEqual({'objectGUID': '123'}, result['ad_data'])
        self.assertEqual('Remove user', result['description'])


class TestRetrieveLdapInfos(unittest.TestCase):

    @patch('libs.sql.database_wrapper.DatabaseWrapper')
    @patch('libs.ldap.ldap_wrapper.LDAPWrapper')
    @patch('libs.user_repository.UserRepository')
    def setUp(self, ldap_mock, database_mock, user_repo_mock):
        self.adsync_mock = build_ad_mock()
        self.adsync_mock._ldap_handler = ldap_mock
        self.adsync_mock._ldap_handler.sync_search.return_value = ({}, {})
        self.adsync_mock._user_repository = user_repo_mock

        self.adsync_mock._database_handler = database_mock
        self.adsync_mock._database_handler.get_last_successful_usn.return_value = 0
        self.adsync_mock._database_handler.set_last_successful_usn = MagicMock()

        self.adsync_mock._config = MagicMock(return_value={'search_nodes': 123})
        self.adsync_mock._send_ldap_infos = MagicMock()

    def test_equal_last_successful_and_highest_comitted(self):
        self.adsync_mock._ldap_handler.get_highest_usn_comitted.return_value = 0
        self.adsync_mock._retrieve_ldap_infos()

    def test_slightly_lower_last_successful_than_highest_comitted(self):
        self.adsync_mock._ldap_handler.get_highest_usn_comitted.return_value = 20
        self.adsync_mock._retrieve_ldap_infos()

    def test_mucho_lower_last_successful_than_highest_comitted(self):
        self.adsync_mock._ldap_handler.get_highest_usn_comitted.return_value = 200000
        self.adsync_mock._retrieve_ldap_infos()


class TestRetryLdapQueries(unittest.TestCase):

    @patch('libs.sql.database_wrapper.DatabaseWrapper')
    @patch('libs.ldap.ldap_wrapper.LDAPWrapper')
    def setUp(self, ldap_mock, database_mock):
        self.adsync_mock = build_ad_mock()
        self.adsync_mock._database_handler = database_mock
        self.adsync_mock._ldap_handler = ldap_mock
        self.adsync_mock._config = MagicMock(return_value={'search_nodes': {'notdeleted': 'test', 'deleted': 'test'}})
        self.adsync_mock._create_sync_list = MagicMock(return_value=[])
        self.adsync_mock._send_ldap_infos = MagicMock(return_value=None)

    def test_no_retry(self):
        self.adsync_mock._database_handler.get_retry_entries.return_value = []
        self.adsync_mock._retry_ldap_queries()

    def test_no_ldap_result(self):
        self.adsync_mock._database_handler.get_retry_entries.return_value = ['123']
        self.adsync_mock._ldap_handler.find_entry_by_object_id.return_value = None

        self.adsync_mock._retry_ldap_queries()

    def test_with_ldap_result(self):
        self.adsync_mock._database_handler.get_retry_entries.return_value = ['123']
        self.adsync_mock._ldap_handler.find_entry_by_object_id.return_value = {'test': 'abc'}
        self.adsync_mock._retry_ldap_queries()


class TestSendLdapInfos(unittest.TestCase):

    @patch('libs.sql.database_wrapper.DatabaseWrapper')
    def setUp(self, database_mock):
        self.adsync_mock = build_ad_mock()
        self.adsync_mock._database_handler = database_mock
        self.adsync_mock._database_handler.add_retry_entry = MagicMock()

    def test_no_syncs(self):
        self.adsync_mock._send_ldap_infos([])

    def test_only_deleted_entries(self):
        self.adsync_mock._send_ldap_infos([{'usn_changed': [0], 'function':  Mock(), 'ad_data': {'objectGUID': [0]}, 'description': 'test'}])


def enabled_user_account_control():
    return ['0']
