#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import os
import unittest
from mock import patch, Mock, MagicMock
from libs.sql.database_wrapper import DatabaseWrapper
import sqlite3


@patch.object(DatabaseWrapper, '_create_database', Mock())
@patch.object(DatabaseWrapper, '_create_tables', Mock())
def build_database_mock():
    if os.path.exists("database.db"):
        os.remove("database.db")
    return DatabaseWrapper()


def build_and_init_database_mock(table_func):
    mock = build_database_mock()
    mock._create_database()
    getattr(mock, table_func)()
    return mock


def reset_database(database):
    database.terminate()
    if os.path.exists("database.db"):
        os.remove("database.db")


def connect_and_fetch(query):
    conn_handle = sqlite3.connect("database.db")
    cursor = conn_handle.cursor()
    cursor.execute(query)
    content = cursor.fetchall()
    cursor.close()
    conn_handle.close()
    return content


class TestCreateDatabase(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_database_mock()

    def tearDown(self):
        reset_database(self.database_mock)

    def test_success(self):
        self.database_mock._create_database()
        self.assertTrue(os.path.exists("database.db"))


class TestCreateAllTables(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_database_mock()
        self.database_mock._create_retry_table = MagicMock()
        self.database_mock._create_users_table = MagicMock()
        self.database_mock._create_usn_table = MagicMock()
        self.database_mock._create_fax_assign_table = MagicMock()
        self.database_mock._create_fax_unassign_table = MagicMock()

    def tearDown(self):
        reset_database(self.database_mock)

    def test_success(self):
        self.database_mock._create_tables()


class TestCreateUsnTable(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_usn_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_create_usn_table(self):
        if not self.database_mock._execute_and_fetch("SELECT name FROM sqlite_master WHERE type='table' AND name='usnInfos'"):
            self.fail()


class TestCreateUserTable(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_users_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_create_users_table(self):
        if not self.database_mock._execute_and_fetch("SELECT name FROM sqlite_master WHERE type='table' AND name='usersInfos'"):
            self.fail()


class TestCreateRetryTable(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_retry_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_create_retry_table(self):
        if not self.database_mock._execute_and_fetch("SELECT name FROM sqlite_master WHERE type='table' AND name='retryInfos'"):
            self.fail()


class TestGetLastSuccessfulUsn(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_usn_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_success(self):
        self.database_mock._execute_and_fetch = MagicMock(return_value=[(10,)])
        self.assertEqual(10, self.database_mock.get_last_successful_usn())

    def test_fail(self):
        self.database_mock._execute_and_fetch = Exception()
        self.assertRaises(Exception, self.database_mock.get_last_successful_usn)


class TestSetLastSuccessfulUsn(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_usn_table')

    def tearDown(self):
        reset_database(self.database_mock)

    @patch.object(DatabaseWrapper, '_cursor', None, create=True)
    def test_success(self):
        self.database_mock.set_last_successful_usn(10)
        self.assertEqual([(10,)], self.database_mock._execute_and_fetch("SELECT lastSuccessfulUSN FROM usnInfos"))

    def test_fail(self):
        self.database_mock.set_last_successful_usn = Exception()
        self.assertRaises(Exception, self.database_mock.set_last_successful_usn, 0)


class TestAddUser(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_users_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_add(self):
        amount_before = len(self.database_mock._execute_and_fetch('SELECT * FROM usersInfos'))
        self.database_mock.add_user('1', 0, 0, 0)
        amount_after = len(self.database_mock._execute_and_fetch('SELECT * FROM usersInfos'))
        self.assertEqual(amount_after, amount_before + 1)

    def test_add_twice_same_user(self):
        self.database_mock.add_user('0', 0, 0, 0)
        self.assertRaises(Exception, self.database_mock.add_user, ('0', 0, 0, 0))

    def test_wrong_parameters(self):
        self.assertRaises(Exception, self.database_mock.add_user, Mock(), None, None)


class TestModifyUser(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_users_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_modify_fax(self):
        try:
            self.database_mock.add_user('0', 0, 0, 0)
        except:
            query = 'INSERT INTO usersInfos VALUES (?,?,?,?)'
            self.database_mock._cursor.execute(query, ['0', 0, 0, 0])
            self.database_mock._connectionHandler.commit()
        self.database_mock.modify_fax('0', 123)
        entry = self.database_mock._execute_and_fetch('SELECT * FROM usersInfos')
        self.assertEqual(123, entry[0][2])

    def test_modify_unexisting_user(self):
        self.assertRaises(Exception, self.database_mock.modify_fax, -1, None)

    def test_wrong_parameters(self):
        self.assertRaises(Exception, self.database_mock.modify_fax, Mock(), None)


class TestRemoveUser(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_users_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_remove_user(self):
        try:
            self.database_mock.add_user('0', 0, 0, 0)
        except:
            query = 'INSERT INTO usersInfos VALUES (?,?,?,?)'
            self.database_mock._cursor.execute(query, ['0', 0, 0, 0])
            self.database_mock._connectionHandler.commit()
        amount_before = len(self.database_mock._execute_and_fetch('SELECT * FROM usersInfos'))
        try:
            self.database_mock.remove_user('0')
        except:
            self.fail()
        amount_after = len(self.database_mock._execute_and_fetch('SELECT * FROM usersInfos'))
        self.assertEqual(amount_after, amount_before - 1)

    def test_remove_twice_same_user(self):
        try:
            self.database_mock.add_user('1', 0, 0, 0)
        except:
            query = 'INSERT INTO usersInfos VALUES (?,?,?,?)'
            self.database_mock._cursor.execute(query, ['1', 0, 0, 0])
            self.database_mock._connectionHandler.commit()
        self.database_mock.remove_user('1')
        self.assertRaises(Exception, self.database_mock.remove_user, '1')

    def test_wrong_parameters(self):
        self.assertRaises(Exception, self.database_mock.remove_user, Mock())


class TestGetUserInfos(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_users_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_with_results(self):
        try:
            self.database_mock.add_user('0', 0, 0, 0)
        except:
            query = 'INSERT INTO usersInfos VALUES (?,?,?,?)'
            self.database_mock._cursor.execute(query, ['0', 0, 0, 0])
            self.database_mock._connectionHandler.commit()
        self.assertEqual({'fax': 0, 'id': 0}, self.database_mock.get_user_infos('0'))

    def test_no_results(self):
        self.assertEqual({}, self.database_mock.get_user_infos("TEST"))


class TestAddRetryEntry(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_retry_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_add(self):
        amount_before = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.database_mock.add_retry_entry('0')
        amount_after = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.assertEqual(amount_after, amount_before + 1)

    def test_add_twice_same_user(self):
        amount_before = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.database_mock.add_retry_entry('1')
        self.database_mock.add_retry_entry('1')
        amount_after = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.assertEqual(amount_after, amount_before + 1)

    def test_wrong_parameters(self):
        self.assertRaises(Exception, self.database_mock.add_retry_entry, Mock(), None, None)


class TestRemoveRetryEntry(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_retry_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_remove_user(self):
        try:
            self.database_mock.add_retry_entry('0')
        except:
            query = 'INSERT INTO retryInfos VALUES (?)'
            self.database_mock._cursor.execute(query, ['0'])
            self.database_mock._connectionHandler.commit()
        amount_before = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.database_mock.remove_retry_entry('0')
        amount_after = len(self.database_mock._execute_and_fetch('SELECT * FROM retryInfos'))
        self.assertEqual(amount_after, amount_before - 1)

    def test_remove_twice_same_user(self):
        try:
            self.database_mock.add_retry_entry('0')
        except:
            query = 'INSERT INTO retryInfos VALUES (?)'
            self.database_mock._cursor.execute(query, ['0'])
            self.database_mock._connectionHandler.commit()
        self.database_mock.remove_retry_entry('0')
        self.assertRaises(Exception, self.database_mock.remove_retry_entry, '0')

    def test_wrong_parameters(self):
        self.assertRaises(Exception, self.database_mock.remove_user, Mock())


class TestGetRetryEntries(unittest.TestCase):

    def setUp(self):
        self.database_mock = build_and_init_database_mock('_create_retry_table')

    def tearDown(self):
        reset_database(self.database_mock)

    def test_with_results(self):
        try:
            self.database_mock.add_retry_entry('0')
        except:
            query = 'INSERT INTO retryInfos VALUES (?)'
            self.database_mock._cursor.execute(query, ['0'])
            self.database_mock._connectionHandler.commit()
        self.assertEqual(['0'], self.database_mock.get_retry_entries())

    def test_no_results(self):
        self.assertEqual([], self.database_mock.get_retry_entries())
