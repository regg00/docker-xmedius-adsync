#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import os
import logging
import sqlite3

from libs.utils.utility import Utility

logger = logging.getLogger(__name__)


#Wrapper around SQL queries
class DatabaseWrapper():

    is_new = False

    def __init__(self):
        self._create_database()
        self._create_tables()

    #In : string (query), array (*args)
    #Out : None
    def _execute_and_commit(self, query, *args):
        try:
            self._cursor.execute(query, args)
            self._connection_handler.commit()
        except Exception, exc:
            str = str(exc) + ". On query : %s" % query
            logger.exception(str)
            raise Exception(str)

    #In : string (query), array (*args)
    #Out : None
    def _execute_and_fetch(self, query, *args):
        self._cursor.execute(query, args)
        return self._cursor.fetchall()

    #In : None
    #Out : None
    def _create_usn_table(self):
        self._execute_and_commit('CREATE TABLE IF NOT EXISTS usnInfos( lastSuccessfulUSN integer DEFAULT 0 );')
        entries = self._execute_and_fetch('SELECT * FROM usnInfos')
        if not len(entries):
            self._execute_and_commit('INSERT INTO usnInfos VALUES(0)')

    #In : None
    #Out : None
    def _create_users_table(self):
        self._execute_and_commit('CREATE TABLE IF NOT EXISTS usersInfos( object_ID TEXT, ID INTEGER, faxNbr INTEGER, groupID INTEGER, PRIMARY KEY (object_ID));')

    #Description : Create the retry table if it doesn't exist
    #In : None
    #Out : None
    def _create_retry_table(self):
        self._execute_and_commit('CREATE TABLE IF NOT EXISTS retryInfos( object_ID TEXT, PRIMARY KEY (object_ID));')

    def _create_fax_assign_table(self):
        self._execute_and_commit('CREATE TABLE IF NOT EXISTS faxAssigns( object_ID TEXT, faxNbr INTEGER, PRIMARY KEY (object_ID));')

    def _create_fax_unassign_table(self):
        self._execute_and_commit('CREATE TABLE IF NOT EXISTS faxUnassigns( object_ID TEXT, faxNbr INTEGER, PRIMARY KEY (object_ID));')

    #In : None
    #Out : None
    def _create_database(self):
        if not os.path.isfile("database.db"):
            self.is_new = True

        self._connection_handler = sqlite3.connect("database.db")
        self._connection_handler.text_factory = str
        self._cursor = self._connection_handler.cursor()
        logger.info("Connected to database.")

    #In : None
    #Out : None
    def _create_tables(self):
        self._create_usn_table()
        self._create_users_table()
        self._create_retry_table()
        self._create_fax_assign_table()
        self._create_fax_unassign_table()

    #In : string (AD ID)
    #Out : None
    def _add_fax_entry(self, tableName, identifier, fax_id):
        if not self._execute_and_fetch('SELECT * FROM %s WHERE object_ID=?' % tableName, identifier):
            self._execute_and_commit('INSERT INTO %s VALUES (?,?)' % tableName, identifier, fax_id)
        else:
            self._execute_and_commit('UPDATE %s SET faxNbr=? WHERE object_ID=?' % tableName, fax_id, identifier)

    #In : string (AD ID)
    #Out : None
    def _remove_fax_entry(self, tableName, identifier):
        self._execute_and_commit('DELETE FROM %s WHERE object_ID=?' % tableName, identifier)

    #In : None
    #Out : list (all entries)
    def _get_fax_entries(self, tableName):
        result = []
        entries = self._execute_and_fetch('SELECT * FROM %s' % tableName)
        for item in entries:
            result.append({'id': item[0], 'fax': item[1]})
        return result

    #In : None
    #Out : integer (USN)
    def get_last_successful_usn(self):
        entry = self._execute_and_fetch('SELECT lastSuccessfulUSN FROM usnInfos')
        try:
            return Utility.get_first(entry[0])
        except:
            raise Exception("Couldn't fetch last successful usn")

    #In : integer (USN)
    #Out : None
    def set_last_successful_usn(self, usn):
        self._execute_and_commit('UPDATE usnInfos set lastSuccessfulUSN=?', str(usn))

    #In : string (AD ID), integer (web ID), integer (web fax id)
    #Out : None
    def add_user(self, identifier, ID, fax_id, group_id):
        self._execute_and_commit('INSERT INTO usersInfos VALUES (?,?,?,?)', identifier, ID, fax_id, group_id)
        if self._cursor.rowcount != 1:
            raise Exception("Add user " + identifier + " failed")

    #In : string (AD ID), integer (new fax ID)
    #Out : None
    def modify_fax(self, identifier, new_fax_id):
        self._execute_and_commit('UPDATE usersInfos SET faxNbr=? WHERE object_ID=?', new_fax_id, identifier)
        if self._cursor.rowcount != 1:
            raise Exception("Modify fax number for user " + identifier + " failed")

    #In : string (AD ID)
    #Out : None
    def remove_user(self, identifier):
        self._execute_and_commit('DELETE FROM usersInfos WHERE object_ID=?', identifier)
        if self._cursor.rowcount != 1:
            raise Exception("Remove user " + identifier + " failed")

    #In : string (AD ID)
    #Out : tuple(integer,integer) (web ID, fax ID)
    def get_user_infos(self, identifier):
        result = {}
        entries = self._execute_and_fetch('SELECT ID,faxNbr FROM usersInfos WHERE object_ID=?', identifier)
        for item in entries:
            result['id'] = item[0]
            result['fax'] = item[1]
        return result

    #In : string (AD ID)
    #Out : None
    def add_retry_entry(self, identifier):
        if not self._execute_and_fetch('SELECT * FROM retryInfos WHERE object_ID=?', identifier):
            self._execute_and_commit('INSERT INTO retryInfos VALUES (?)', identifier)

    #In : string (AD ID)
    #Out : None
    def remove_retry_entry(self, identifier):
        self._execute_and_commit('DELETE FROM retryInfos WHERE object_ID=?', identifier)
        if self._cursor.rowcount != 1:
            raise Exception("Remove user " + identifier + " failed")

    #In : None
    #Out : list (all entries)
    def get_retry_entries(self):
        result = []
        entries = self._execute_and_fetch('SELECT * FROM retryInfos')
        for item in entries:
            result.append(item[0])
        return result

    def add_fax_assign_entry(self, identifier, fax_id):
        self._add_fax_entry('faxAssigns', identifier, fax_id)

    def remove_fax_assign_entry(self, identifier):
        self._remove_fax_entry('faxAssigns', identifier)

    def get_fax_assign_entries(self):
        return self._get_fax_entries('faxAssigns')

    def add_fax_unassign_entry(self, identifier, fax_id):
        self._add_fax_entry('faxUnassigns', identifier, fax_id)

    def remove_fax_unassign_entry(self, identifier):
        self._remove_fax_entry('faxUnassigns', identifier)

    def get_fax_unassign_entries(self):
        return self._get_fax_entries('faxUnassigns')

    def terminate(self):
        try:
            Utility.permissive_execute(self._cursor.close)
            Utility.permissive_execute(self._connection_handler.close)
        except:
            pass
