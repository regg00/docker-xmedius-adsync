#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import unittest
from mock import patch, Mock, MagicMock
from libs.user_repository import UserRepository
from libs.http.portal_wrapper import PortalWrapper


@patch('libs.sql.database_wrapper.DatabaseWrapper')
@patch.object(PortalWrapper, '__init__', Mock(return_value=None))
def build_user_repo_mock(database_mock):
    database_mock.is_new = False
    return UserRepository(None, database_mock)


class TestInit(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()

    def test_instance_created(self):
        self.assertEqual(True, isinstance(self.user_repo, UserRepository))


class TestRepopulateDatabase(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()

    def test_no_users(self):
        self.user_repo._http_handler.get_all_users = MagicMock(return_value=None)
        self.user_repo.repopulate_database()

    def test_with_users(self):
        self.user_repo._http_handler.get_all_users = MagicMock(return_value=[{'external_id': '1', 'id': '2', 'main_fax_number': '3', 'group_id': '4'}])
        self.user_repo._http_handler.get_default_fax_and_all_faxes = MagicMock(return_value=(None, None))
        self.user_repo._database_handler.add_user = MagicMock()
        self.user_repo.repopulate_database()


class TestAddUser(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()

    def test_no_data(self):
        self.assertRaises(Exception, self.user_repo.add_user, {})

    def test_user_already_exist(self):
        self.user_repo.check_user_exist = MagicMock()
        self.assertRaises(Exception, self.user_repo.add_user, {'objectGUID': [0]})

    def test_no_user_found(self):
        self.user_repo.check_user_exist = MagicMock(return_value=None)
        self.user_repo._database_handler.add_user = MagicMock()
        self.user_repo._http_handler.request_create_user = MagicMock(return_value=(None, None, None, None))
        self.user_repo.add_user({'objectGUID': [0]})


class TestUpdateUser(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()

    def test_no_data(self):
        self.assertRaises(Exception, self.user_repo.update_user, {})

    def test_no_user_found(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value=None)
        self.assertRaises(Exception, self.user_repo.update_user, {'objectGUID': [0]})

    def test_user_found_and_no_new_fax_id(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value={'id': 123})
        self.user_repo._http_handler.request_modify_user = MagicMock(return_value=(None, None, None))
        self.assertEqual(123, self.user_repo.update_user({'objectGUID': [0]}))

    def test_user_found_and_new_fax_id(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value={'id': 123})
        self.user_repo._database_handler.modify_fax = MagicMock()
        self.user_repo._http_handler.request_modify_user = MagicMock(return_value='456')
        self.assertEqual(123, self.user_repo.update_user({'objectGUID': [0]}))


class TestDeleteUser(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()

    def test_no_data(self):
        self.assertRaises(Exception, self.user_repo.delete_user, {})

    def test_no_user_found(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value=None)
        self.assertRaises(Exception, self.user_repo.delete_user, {'objectGUID': [0]})

    def test_user_found(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value={'id': 123})
        self.user_repo._database_handler.remove_user = MagicMock()
        self.user_repo._http_handler.request_delete_user = MagicMock()
        self.assertEqual(123, self.user_repo.delete_user({'objectGUID': [0]}))


class TestCheckUserExist(unittest.TestCase):

    def setUp(self):
        self.user_repo = build_user_repo_mock()
        self.user_repo._database_handler.remove_user = MagicMock()

    def test_exist_in_database_not_in_portal(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value={'id': 0})
        self.user_repo._http_handler.get_user_by_id = MagicMock(return_value=None)
        self.assertEquals(False, self.user_repo.check_user_exist(None))

    def test_exist_in_database_and_portal(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value={'id': 0})
        self.user_repo._http_handler.get_user_by_id = MagicMock(return_value=True)
        self.assertEquals(True, self.user_repo.check_user_exist(None))

    def test_not_exist_in_database(self):
        self.user_repo._database_handler.get_user_infos = MagicMock(return_value=None)
        self.assertEquals(False, self.user_repo.check_user_exist(None))
