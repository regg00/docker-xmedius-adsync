#!/usr/bin/python

#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

# Version 1.0.4

import sys
import os

# Add the local third party folders to the search path
_adsync_root_folder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_adsync_root_folder, 'third_party', 'mock-1.0b1'))
sys.path.append(os.path.join(_adsync_root_folder, 'third_party', 'python-ldap-2.4.10.win32-py2.7'))
sys.path.append(os.path.join(_adsync_root_folder, 'third_party', 'PyYAML-3.10.win32-py2.7'))

from libs.utils.utility import Utility
from libs.ldap.ldap_wrapper import LDAPWrapper
from libs.sql.database_wrapper import DatabaseWrapper
from libs.user_repository import UserRepository
from libs.list_synchronizer import ListSynchronizer

page_size = 10000

config_dir = _adsync_root_folder + os.sep + 'config' + os.sep
default_yaml_file = 'default.yaml'

import logging
logger = logging.getLogger('adsync')
logger.addHandler(logging.NullHandler())

# Synchronization manager
class ADSync():
    _resync = False

    #In : list (command-line args)
    #Out : bool
    def __init__(self):
        try:
            self._load_ressources()
        except Exception, e:
            logger.exception(e)
            sys.exit()

    #In : None
    #Out : None
    def _load_ressources(self):
        command_args = []
        for arg in sys.argv:
            command_args.append(arg.lower())

        # If we have 'r' command-line arg, full resync
        if 'r' in command_args:
            self._resync = True

        self._load_config(command_args)
        self._load_modules()

    #In : None
    #Out : None
    def _load_modules(self):
        self._ldap_handler = LDAPWrapper(self._config['active_directory'], page_size)
        self._database_handler = DatabaseWrapper()
        self._user_repository = UserRepository(self._config, self._database_handler)

    #In : list (command-line args)
    #Out : None
    def _load_config(self, command_args):
        config_path = config_dir + default_yaml_file
        if len(command_args) > 1:
            path_from_config_dir = config_dir + command_args[1]
            if os.path.isfile(path_from_config_dir):
                config_path = path_from_config_dir
            elif os.path.isfile(command_args[1]):
                config_path = command_args[1]
        self._config = Utility.parse_yaml(config_path)
        logger.info('Config loaded from: %s' % config_path)

    #In : None
    #Out : None
    def _stop_sync(self):
        self._ldap_handler.terminate()
        self._user_repository.terminate()

    #In : list (command-line args)
    #Out : None
    def _start_sync(self):
        if self._resync:
            self._database_handler.set_last_successful_usn(0)
        self._retry_ldap_queries()
        self._retrieve_ldap_infos()

    #In : dict (not_deleted_entries), dict (deleted_entries)
    #Out : dict (sync_list)
    def _create_sync_list(self, not_deleted_entries, deleted_entries):
        return ListSynchronizer(self._user_repository).sync(not_deleted_entries, deleted_entries)

    #In : None
    #Out : None
    def _retrieve_ldap_infos(self):
        logger.info("Retrieve LDAP info")
        last_successful_usn = self._database_handler.get_last_successful_usn()

        highest_usn = self._ldap_handler.get_highest_usn_comitted()
        while last_successful_usn < highest_usn:
            last_successful_usn += 1
            possible_max_usn = last_successful_usn + page_size - 1
            target_usn = possible_max_usn if possible_max_usn < highest_usn else highest_usn

            not_deleted_entries, deleted_entries = self._ldap_handler.sync_search(last_successful_usn, target_usn, self._config['active_directory']['search_nodes'])

            sync_list = self._create_sync_list(not_deleted_entries, deleted_entries)
            self._send_ldap_infos(sync_list)

            #if we synced all our data, lastSuccessful is targetUSN
            self._database_handler.set_last_successful_usn(target_usn)
            last_successful_usn = target_usn

    #In : None
    #Out : None
    def _retry_ldap_queries(self):
        retry_list = self._database_handler.get_retry_entries()
        if retry_list:
            logger.info('Retry procedure begins on %s entry(ies)' % len(retry_list))
            not_deleted_entries = {}
            deleted_entries = {}
            for entry in retry_list:
                try:
                    result = self._ldap_handler.find_entry_by_object_id(entry, self._config['active_directory']['search_nodes']['query_for_users'])
                    if result:
                        not_deleted_entries.update(result)
                    else:
                        result = self._ldap_handler.find_entry_by_object_id(entry, self._config['active_directory']['search_nodes']['query_for_deleted_users'])
                        if result:
                            deleted_entries.update(result)
                        else:
                            #TODO faire quelque chose avec les entres que l'on ne trouve nulle part
                            pass
                except:
                    pass
            sync_list = self._create_sync_list(not_deleted_entries, deleted_entries)
            for entry in sync_list:
                self._database_handler.remove_retry_entry(Utility.get_first(entry['ad_data']['objectGUID']))
            self._send_ldap_infos(sync_list, True)
            logger.info('Retry procedure ends')

    #In : dictionary (notDeletedEntries), dictionary (deletedEntries)
    #Out : None
    def _send_ldap_infos(self, sync_list, from_retry=False):
        if sync_list:
            sync_list.sort(key=lambda x: [int(y) for y in x['usn_changed']])
            for entry in sync_list:
                try:
                    logger.info("New operation (usn=%s) on user : %s " % (entry['usn_changed'], Utility.get_first(entry['ad_data']['distinguishedName'])))
                    user_id = entry['function'](entry['ad_data'])
                    if user_id:
                        logger.info(entry['description'] + ' successful with portal id: ' + str(user_id))
                except Exception, e:
                    logger.error(entry['description'] + ' failure: %s' % str(e))
                    if not isinstance(e, Utility.UnRetryableException):
                        self._database_handler.add_retry_entry(Utility.get_first(entry['ad_data']['objectGUID']))
                if not from_retry:
                    self._database_handler.set_last_successful_usn(entry['usn_changed'])
                logger.info(" -- \n")

    #In : None
    #Out : None
    def run(self):
        logger.info('Synchronization begins')
        try:
            self._start_sync()
            self._stop_sync()
        except Exception, e:
            logger.exception(e)
        logger.info('Synchronization ends')

if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig("config/logging.conf", disable_existing_loggers=False)
    logger = logging.getLogger('adsync')

    sync = ADSync()
    sync.run()
