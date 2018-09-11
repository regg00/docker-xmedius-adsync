#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import unittest
from libs.http.portal_wrapper import PortalWrapper
from libs.http.http_requester import HTTPRequester
from libs.utils.utility import Utility
from mock import patch, Mock, MagicMock


@patch.object(PortalWrapper, '_cache_faxes_and_groups', Mock())
@patch.object(HTTPRequester, '__init__', Mock(return_value=None))
def build_portal_mock(config={'fax_service': {'address': None, 'access_token': None}}):
    return PortalWrapper(config)


class TestInit(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_no_config(self):
        self.assertRaises(Exception, self.portal_mock, "")

    def test_with_config(self):
        self.assertEqual(True, isinstance(self.portal_mock, PortalWrapper))


class TestGetDefaultAndAssignedGroupValues(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_list_exist(self):
        self.portal_mock._default_group = 123
        self.portal_mock._assigned_groups = 456
        self.assertEqual((123, 456), self.portal_mock._get_default_and_assigned_group_values())

    def test_list_not_exist(self):
        self.portal_mock._assigned_groups = None
        self.portal_mock._get_default_and_assigned_values = MagicMock(return_value=(123, 456))
        self.assertEqual((123, 456), self.portal_mock._get_default_and_assigned_group_values())


class TestGetDefaultAndAssignedFaxValues(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_list_exist(self):
        self.portal_mock._default_fax = 123
        self.portal_mock._assigned_faxes = 456
        self.assertEqual((123, 456), self.portal_mock._get_default_and_assigned_fax_values())

    def test_list_not_exist(self):
        self.portal_mock._assigned_faxes = None
        self.portal_mock._get_default_and_assigned_values = MagicMock(return_value=(123, 456))
        self.assertEqual((123, 456), self.portal_mock._get_default_and_assigned_fax_values())


class TestGetDefaultAndAssignedValues(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()
        self.portal_mock._enterprise_url = MagicMock()

    def test_success(self):
        self.portal_mock._get_portal_data = MagicMock(return_value={'default': 123, 'groups': 456})
        self.assertEqual((123, 456), self.portal_mock._get_default_and_assigned_values('groups'))


class TestGetAllUsers(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()
        self.portal_mock._enterprise_url = MagicMock()

    def test_list_not_exist(self):
        self.portal_mock._get_portal_data = MagicMock(return_value={'user': 123})
        self.assertEqual({'user': 123}, self.portal_mock.get_all_users())

    def test_list_exist(self):
        self.portal_mock._all_users = {'user': 123}
        self.assertEqual({'user': 123}, self.portal_mock.get_all_users())


class TestGetUserById(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_no_id_request(self):
        self.portal_mock._users_by_id = {'10':'test'}
        self.assertEqual(None, self.portal_mock.get_user_by_id(0))

    def test_id_request(self):
        self.portal_mock._users_by_id = {'10':'test'}
        self.portal_mock._get_portal_data = MagicMock(return_value='test2')
        self.assertEqual('test2', self.portal_mock.get_user_by_id(10))


class TestMatchOrSetDefault(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_default_value(self):
        self.assertEqual('default', self.portal_mock.match_or_set_default({}, 'default', ''))

    def test_matched_value(self):
        self.assertEqual('key2',
                          self.portal_mock.match_or_set_default({'key1': 'value1', 'key2': 'value2'}, '', 'value2'))


class TestReadResponse(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_success(self):
        data = {'result': 123}
        Utility.decode_json = MagicMock(return_value=data)
        self.assertEqual({'result': 123}, self.portal_mock.read_response(data))

    def test_fail(self):
        data = {}
        Utility.decode_json = MagicMock(return_value=data)
        self.assertRaises(Exception, self.portal_mock.read_response, data)


class TestReadDataResponse(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()

    def test_success(self):
        data = {'result': 123, 'data': 'test'}
        Utility.decode_json = MagicMock(return_value=data)
        self.assertEqual({'result': 123, 'data': 'test'}, self.portal_mock.read_response(data))

    def test_fail(self):
        data = {}
        Utility.decode_json = MagicMock(return_value=data)
        self.assertRaises(Exception, self.portal_mock.read_response, data)


class TestRequestCreate(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()
        self.portal_mock._assign_fax = MagicMock()
        self.portal_mock._enterprise_url = MagicMock()
        self.portal_mock._requester.post = MagicMock(return_value=None)

    def test_success(self):
        self.portal_mock.match_attributes = MagicMock(return_value={'username': 'a', 'email': 'b', 'language': 'c'})
        self.portal_mock.read_data_response = MagicMock(return_value={'id': '1'})
        self.assertEqual(('1', None, None, None), self.portal_mock.request_create_user({}))

    def test_fail(self):
        self.portal_mock.match_attributes = MagicMock(return_value={})
        self.portal_mock.read_data_response = MagicMock(return_value={})
        self.assertRaises(Exception, self.portal_mock.request_create_user, {})


class TestRequestModify(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()
        self.portal_mock._enterprise_url = MagicMock(return_value='url')
        self.portal_mock.get_user_by_id = MagicMock(return_value={'username': 'old_username',
                                                                  'main_fax_number_id': 'old_fax',
                                                                  'id': 'old_id',
                                                                  'email': 'old_email'})
        self.portal_mock._requester.put = MagicMock(return_value='response')
        self.read_response = MagicMock()

    def test_no_modification(self):
        self.portal_mock.match_attributes = MagicMock(return_value={'username': 'old_username',
                                                                    'main_fax_number_id': 'old_fax',
                                                                    'id': 'old_id',
                                                                    'email': 'old_email'})
        self.assertEqual((None, None, None), self.portal_mock.request_modify_user({}, {'id': 'new_id'}))

    def test_without_fax_modification_1(self):
        self.portal_mock.match_attributes = MagicMock(return_value={'username': 'new_username',
                                                                    'main_fax_number_id': 'old_fax',
                                                                    'id': 'new_id',
                                                                    'email': 'new_email'})
        self.assertEqual((None, None, None), self.portal_mock.request_modify_user({}, {'id': 'new_id'}))

    def test_without_fax_modification_2(self):
        self.portal_mock.match_attributes = MagicMock(return_value={'username': 'old_username',
                                                                    'main_fax_number_id': 'old_fax',
                                                                    'id': 'old_id',
                                                                    'email': 'old_email'})
        self.assertEqual((None, None, None), self.portal_mock.request_modify_user({}, {'id': 'new_id'}))


class TestRequestDeleteFunction(unittest.TestCase):

    def setUp(self):
        self.portal_mock = build_portal_mock()
        self.portal_mock._enterprise_url = MagicMock(return_value='url')
        self.portal_mock._requester.delete = MagicMock(return_value=None)
        self.portal_mock.read_response = MagicMock()

    @patch.object(HTTPRequester, 'post', Mock(return_value=None))
    def test_success(self):
        self.portal_mock.request_delete_user({'id': '1'})

    @patch.object(HTTPRequester, 'post', Mock(return_value=None))
    def test_success_with_new_fax(self):
        self.portal_mock._unassign_fax = MagicMock()
        self.portal_mock.request_delete_user({'id': '1', 'fax': '2'})
