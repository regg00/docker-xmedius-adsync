#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import logging

from libs.utils.utility import Utility
from http.portal_wrapper import PortalWrapper

logger = logging.getLogger(__name__)


class UserRepository():

    #In : Config (config_data), DatabaseWrapper (database_handle)
    #Out : None
    def __init__(self, config_data, database_handle):

        self._http_handler = PortalWrapper(config_data)
        self._database_handler = database_handle

        self._retry_fax_unassigns()
        self._retry_fax_assigns()

        if self._database_handler.is_new:
            self.repopulate_database()

    def _retry_fax_assigns(self):
        retry_list = self._database_handler.get_fax_assign_entries()
        if retry_list:
            logger.info('Attempting fax assign on %s entry(ies)' % len(retry_list))
            for entry in retry_list:
                try:
                    self._http_handler.assign_fax(entry['fax'], entry['id'])
                    self._database_handler.remove_fax_assign_entry(entry['id'])
                except:
                    continue

    def _retry_fax_unassigns(self):
        retry_list = self._database_handler.get_fax_unassign_entries()
        if retry_list:
            logger.info('Attempting fax unassign on %s entry(ies)' % len(retry_list))
            for entry in retry_list:
                try:
                    self._http_handler.unassign_fax(entry['fax'], entry['id'])
                    self._database_handler.remove_fax_unassign_entry(entry['id'])
                except:
                    continue

    def _manage_fax_assign_list(self, object_id, fax_number):
        if fax_number is not None:
            self._database_handler.add_fax_assign_entry(object_id, fax_number)
        else:
            self._database_handler.remove_fax_assign_entry(object_id)

    def _manage_fax_unassign_list(self, object_id, fax_number):
        if fax_number is not None:
            self._database_handler.add_fax_unassign_entry(object_id, fax_number)
        else:
            self._database_handler.remove_fax_unassign_entry(object_id)

    #In : None
    #Out : None
    def repopulate_database(self):
        users = self._http_handler.get_all_users()
        if users:
            for entry in users:
                self._database_handler.add_user(entry['external_id'], entry['id'], entry['main_fax_number'], entry['group_id'])

    #In : dict (data)
    #Out : user_id
    def add_user(self, data):
        if not self.check_user_exist(data['objectGUID'][0]):
            user_id, fax_id, group_id, failed_fax_assign_nbr = self._http_handler.request_create_user(data)
            self._database_handler.add_user(data['objectGUID'][0], user_id, fax_id, group_id)
            self._manage_fax_assign_list(user_id, failed_fax_assign_nbr)
            return user_id
        else:
            raise Utility.UnRetryableException("User already exist in database.")

    #In : dict (data)
    #Out : user_id
    def update_user(self, data):
        user_infos = self._database_handler.get_user_infos(data['objectGUID'][0])
        if user_infos:
            logger.info("Update user info %s" % user_infos)
            new_fax_id, failed_fax_unassign_nbr, failed_fax_assign_nbr = self._http_handler.request_modify_user(data, user_infos)
            if new_fax_id:
                self._database_handler.modify_fax(data['objectGUID'][0], str(new_fax_id))
            self._manage_fax_unassign_list(user_infos['id'], failed_fax_unassign_nbr)
            self._manage_fax_assign_list(user_infos['id'], failed_fax_assign_nbr)
            return user_infos['id']
        else:
            raise Utility.UnRetryableException("User does not exist in database.")

    #In : dict (data)
    #Out : user_id
    def delete_user(self, data):
        user_infos = self._database_handler.get_user_infos(data['objectGUID'][0])
        if user_infos:
            self._http_handler.request_delete_user(user_infos)
            self._database_handler.remove_user(data['objectGUID'][0])
            return user_infos['id']
        else:
            raise Utility.UnRetryableException("User does not exist in database.")

    #In : string (identifier)
    #Out : user_id
    def check_user_exist(self, identifier):
        exist = False
        user_infos = self._database_handler.get_user_infos(identifier)
        if user_infos:
            if self._http_handler.get_user_by_id(user_infos['id']):
                exist = True
            else:
                self._database_handler.remove_user(identifier)
        return exist

    def terminate(self):
        Utility.permissive_execute(self._database_handler.terminate)
