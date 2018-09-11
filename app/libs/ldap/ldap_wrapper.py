#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import base64
import logging

from libs.utils.utility import Utility
from libs.ldap.exclusion_filter import LdapExclusionFilter
import ldap
import ldap.filter as Filter
from ldap.controls import SimplePagedResultsControl

LDAP_SERVER_SHOW_DELETED_OID = '1.2.840.113556.1.4.417'
LDAP_CONTROL_PAGE_OID = '1.2.840.113556.1.4.319'

logger = logging.getLogger(__name__)


#Wrapper around ldap queries
class LDAPWrapper():

    #In : None
    #Out : None
    def __init__(self, ad_infos, page_size):
        self._page_size = page_size
        self._highest_committed_usn = -1
        self.connect_to_ldap_server(ad_infos)

    #In : None
    #Out : None
    def get_highest_usn_comitted(self):

        if self._highest_committed_usn == -1:

            base_dn = ""
            search_scope = ldap.SCOPE_BASE

            try:
                msgid = self._server_handler.search(base_dn, search_scope)
                result_type, result_data = self._server_handler.result(msgid, 0)
                if result_type == ldap.RES_SEARCH_ENTRY:
                    self._highest_committed_usn = int((result_data[0][1]['highestCommittedUSN'][0]))
            except:
                raise Exception("Could not retrieve highest USN")

        return self._highest_committed_usn

    #In : integer (min_USN), integer (max_USN)
    #Out : None
    def sync_search(self, min_USN, max_USN, search_nodes):
        logger.debug("Syncing entries by usn %s - %s" % (min_USN, max_USN))
        not_deleted_entries = {}
        deleted_entries = {}
        if search_nodes['query_for_users']:
            not_deleted_entries = self._find_entries_by_usn(min_USN, max_USN, search_nodes['query_for_users'], [])
        if search_nodes['query_for_deleted_users']:
            deleted_entries = self._find_entries_by_usn(min_USN, max_USN, search_nodes['query_for_deleted_users'], [LDAP_SERVER_SHOW_DELETED_OID])
        return not_deleted_entries, deleted_entries

    #In : string (object_id)
    #Out : dictionary (AD entry)
    def find_entry_by_object_id(self, object_id, search_nodes):
        object_id = base64.b16decode(object_id)
        object_id = Filter.escape_filter_chars(object_id, escape_mode=0)
        ctrl_response = ldap.controls.RequestControl(LDAP_SERVER_SHOW_DELETED_OID, True)
        for entry in search_nodes:
            msgid = self._server_handler.search_ext(entry['base'], ldap.SCOPE_SUBTREE, 'objectGUID=%s' % object_id, serverctrls=[ctrl_response])
            result_type, result_data = self._server_handler.result(msgid)
            if result_type == ldap.RES_SEARCH_RESULT:
                try:
                    result_data = Utility.get_first(result_data)
                    new_item = {'ad_data': result_data[1], 'usn_changed': Utility.get_first(result_data[1]['uSNChanged'])}
                    new_item['ad_data']['objectGUID'][0] = base64.b16encode(new_item['ad_data']['objectGUID'][0])
                    return {entry['base']: [new_item]}
                except:
                    pass

    #In : None
    #Out : None
    def connect_to_ldap_server(self, AD_infos):
        try:
            ldapURI = 'ldap://%s:%s' % (AD_infos['address'], AD_infos['port'])
            self._server_handler = ldap.initialize(ldapURI)
            self._server_handler.protocol_version = 3
            self._server_handler.set_option(ldap.OPT_REFERRALS, 0)

            self._server_handler.simple_bind_s(AD_infos['username'], AD_infos['password'])
            logger.info("Link established with directory: %s Port : %i." % (AD_infos['address'], AD_infos['port']))
        except Exception, e:
            logger.exception("Failed to connect to ldap server")
            raise Exception("Failed to connect to ldap server : %s" % str(e))

    def terminate(self):
        Utility.permissive_execute(self._server_handler.unbind_s)

    # Filters out exclusiosn if present.
    # Exclusions is a list of attributes (eg mail) and exclusion filters with wildcards (eg *administrators*)
    def _filter_exclusions(self, query_params, results):
        exclusion_filter = LdapExclusionFilter(query_params)
        return exclusion_filter.filter(results)

    #In : string (base_dn), string (search_scope), string (search_filter), array (control_codes)
    #Out : array (ldap result)
    def _ldap_page_search(self, base_dn, search_scope, search_filter, control_codes):

        results = []
        control_args = []

        page_handler = SimplePagedResultsControl(True, self._page_size, '')
        control_args.append(page_handler)

        for code in control_codes:
            ctrl_response = ldap.controls.RequestControl(code, True)
            control_args.append(ctrl_response)

        while True:
            msgid = self._server_handler.search_ext(base_dn, search_scope, search_filter, serverctrls=control_args)
            result_type, result_data, rmsgid, controls = self._server_handler.result3(msgid)

            if not result_data:
                break

            if result_type == ldap.RES_SEARCH_RESULT:
                for r in result_data:
                    results.append(r)

            page_controls = [c for c in controls if c.controlType == LDAP_CONTROL_PAGE_OID]

            if page_controls:
                page_handler.size, page_handler.cookie = (page_controls[0].size, page_controls[0].cookie)
                if not page_handler.cookie:
                    break
            else:
                break
        return results

    #In : string (base_filter), array (additional_filters)
    #Out : string (reformatted filter)
    def _format_ldap_filter(self, base_filter, additional_filters):
        #Remove enclosing parentheses
        if base_filter.startswith('(') and base_filter.endswith(')'):
            base_filter = base_filter[1:-1]
        new_filter = '(' + base_filter + ')'
        for fltr in additional_filters:
            new_filter += '(' + fltr + ')'
        return '(&' + new_filter + ')'

    #In : integer (min_USN), integer (max_USN), array (search_nodes), array (control_codes)
    #Out : dictionary (AD entries)
    def _find_entries_by_usn(self, min_USN, max_USN, search_nodes, control_codes):
        entries = {}
        for entry in search_nodes:

            base_dn = entry['base']

            if entry['scope'] == 'BASE':
                search_scope = ldap.SCOPE_BASE
            elif entry['scope'] == 'ONELEVEL':
                search_scope = ldap.SCOPE_ONELEVEL
            else:
                search_scope = ldap.SCOPE_SUBTREE

            additional_filters = []
            additional_filters.append('uSNChanged>=' + str(min_USN))
            additional_filters.append('uSNChanged<=' + str(max_USN))

            search_filter = self._format_ldap_filter(entry['filter'], additional_filters)

            results = self._ldap_page_search(base_dn, search_scope, search_filter, control_codes)
            results = self._filter_exclusions(entry, results)

            #Initialize dictionary to empty values
            entries[base_dn] = []

            for item in results:
                if item[0] is None:
                    logger.debug("Got referrals during search (%s), skipping it" % item[1])
                    continue

                new_item = {'ad_data': item[1], 'usn_changed': item[1]['uSNChanged'][0]}
                new_item['ad_data']['objectGUID'][0] = base64.b16encode(new_item['ad_data']['objectGUID'][0])
                entries[base_dn].append(new_item)

            if not entries[base_dn]:
                entries.pop(base_dn, None)
        return entries
