#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import collections
import logging

from libs.utils.utility import Utility
from libs.http.http_requester import HTTPRequester
from libs.http.attributes_matcher import AttributesMatcher

logger = logging.getLogger(__name__)


class PortalWrapper():
    _users_by_id = {}
    _all_users = {}
    _assigned_faxes = {}
    _default_fax = None
    _assigned_groups = {}
    _default_group = None

    #In : Config (config_data)
    #Out : user_id
    def __init__(self, config_data):
        self._config_data = config_data
        self.disable_welcome_email = self._config_data['fax_service'].get('disable_emails', False)
        self._requester = HTTPRequester(self._config_data['fax_service']['address'],
                                        self._config_data['fax_service']['access_token'])
        self._cache_faxes_and_groups()

    #In : string (url)
    #Out : converted type (response)
    def _get_portal_data(self, url):
        response = self._requester.get(url)
        return self.read_data_response(response)

    #In : string (portal id), string (fax id)
    #Out : None
    def assign_fax(self, portal_id, fax_id):
        if not self.is_fax_main_or_shared(fax_id):
            self._requester.post('fax_numbers/%s/associate' % fax_id, Utility.encode_json({'user_id': portal_id}))

    #In : string (portal id), string (fax id)
    #Out : None
    def unassign_fax(self, portal_id, fax_id):
        self._requester.post('fax_numbers/%s/disassociate' % fax_id, Utility.encode_json({'user_id': portal_id}))

    #In : None
    #Out : None
    def _cache_faxes_and_groups(self):
        self._get_default_and_assigned_group_values()
        self._get_default_and_assigned_fax_values()

    #In : None
    #Out : dict (_default_group) dict(_assigned_groups)
    def _get_default_and_assigned_group_values(self):
        if not self._assigned_groups:
            self._default_group, self._assigned_groups = self._get_default_and_assigned_values('groups')
        return self._default_group, self._assigned_groups

    #In : None
    #Out : dict (_default_fax) dict(_assigned_faxes)
    def _get_default_and_assigned_fax_values(self):
        if not self._assigned_faxes:
            self._default_fax, self._assigned_faxes = self._get_default_and_assigned_values('fax_numbers')
        return self._default_fax, self._assigned_faxes

    #In : value_name
    #Out : string (data['default']) dict(data[value_name])
    def _get_default_and_assigned_values(self, value_name):
        data = self._get_portal_data(value_name)
        return data['default'], data[value_name]

    #In : None
    #Out : string (_all_users)
    def get_all_users(self):
        if not self._all_users:
            self._all_users = self._get_portal_data("users")
        return self._all_users

    #In : int (id)
    #Out : dict (_users_by_id[id])
    def get_user_by_id(self, id):
        try:
            if id not in self._users_by_id:
                url = "users/%i" % id
                self._users_by_id[id] = self._get_portal_data(url)
            return self._users_by_id[id]
        except:
            return None

    #In : dict (matched_dict), string (default_value), string (compared_value)
    #Out : dict (_users_by_id[id])
    def match_or_set_default(self, matched_dict, default_value, compared_value, comparator=lambda x, y: x.lower() == y.lower()):
        results = [k for k, v in matched_dict.iteritems() if comparator(v, compared_value)]
        if results:
            result = Utility.get_first(results)
        else:
            result = default_value

        return result

    #In : dict (data)
    #Out : dict (data)
    def read_data_response(self, data):
        return self.read_response(data)['data']

    #In : dict (data)
    #Out : dict (data)
    def read_response(self, data):
        data = Utility.decode_json(data)
        if not data["result"]:
            raise Exception("Portal exception : %s " % convert_error_map_to_string(data["errors"]))
        return data

    #In : dict (ad_data)
    #Out : integer (user_id),  integer (fax_id), integer (group_id)
    def request_create_user(self, ad_data):
        failed_assign = None
        logger.info("Creating user...")
        attributes = self.match_attributes(ad_data, {})
        attributes.setdefault('main_fax_number_id', self._default_fax)
        attributes.setdefault('group_id', self._default_group)
        attributes['disable_welcome_email'] = self.disable_welcome_email

        if not Utility.verify_contain_keys(attributes, ["username"]):
            raise Utility.UnRetryableException("Skipping user %s as username is not present. This user will not be tried again until it is modified." % ad_data['cn'])
        if not Utility.verify_contain_keys(attributes, ["email"]):
            raise Utility.UnRetryableException("Skipping user %s as email is not present. This user will not be tried again until it is modified." % ad_data['cn'])

        encoded_attributes = Utility.encode_json({'user': attributes})
        logger.info("Create user attributes=%s" % encoded_attributes)
        response = self._requester.post("users", encoded_attributes)
        data = self.read_data_response(response)

        logger.info("create_user: fax=%s, default=%s" % (attributes['main_fax_number_id'], self._default_fax))
        if not Utility.permissive_execute(self.assign_fax, data['id'], attributes['main_fax_number_id']):
            failed_assign = attributes['main_fax_number_id']
        return data['id'], attributes['main_fax_number_id'], attributes['group_id'], failed_assign

    #In : dict (ad_data), array (user_info)
    #Out : integer (new fax_id) OR None
    def request_modify_user(self, ad_data, user_infos):
        data = self.get_user_by_id(user_infos['id'])
        if data:
            failed_unassign = None
            failed_assign = None
            previous_main_fax_number_id = data['main_fax_number_id']
            attributes = self.match_attributes(ad_data, data)
            logger.info("attributes modify=%s" % attributes)
            logger.info("modified data=%s" % data)
            Utility.remove_keys(attributes, ("username", "email", "id", "external_id"))
            encoded_attributes = Utility.encode_json({'user': attributes})

            response = self._requester.put("users/%s" % user_infos['id'], encoded_attributes)
            self.read_response(response)
            try:
                if not self.is_same_fax_number(attributes['main_fax_number_id'], previous_main_fax_number_id):
                    logger.info("Fax numbers differ... previous was %s, new is %s" % (previous_main_fax_number_id, attributes['main_fax_number_id']))
                    if not Utility.permissive_execute(self.unassign_fax, user_infos['id'], previous_main_fax_number_id):
                        failed_unassign = previous_main_fax_number_id
                    if (not attributes['main_fax_number_id'] is None) and attributes['main_fax_number_id'] != self._default_fax:
                        if not Utility.permissive_execute(self.assign_fax, user_infos['id'], attributes['main_fax_number_id']):
                            failed_assign = attributes['main_fax_number_id']
                    return attributes['main_fax_number_id'], failed_unassign, failed_assign
            except:
                pass
            return None, failed_unassign, failed_assign
        else:
            raise Exception("Could not retrieve user information from portal")

    #In : array (user_infos)
    #Out : None
    def request_delete_user(self, user_infos):
        response = self._requester.delete("users/%s" % user_infos['id'])
        self.read_response(response)

    def is_same_fax_number(self, fax1, fax2):
        if(fax1 is None):
            fax1 = ''
        if(fax2 is None):
            fax2 = ''
        return str(fax1) == str(fax2)

    def is_fax_main_or_shared(self, fax):
        if fax is None:
            return False
        else:
            return fax == self._default_fax or self._assigned_faxes[fax]['shared']

    def match_attributes(self, ad_data, attributes):
        return self._attributes_matcher().match_attributes(ad_data, attributes)

    def _attributes_matcher(self):
        return AttributesMatcher(self._config_data, self._default_group, self._assigned_groups, self._default_fax, self._assigned_faxes)


def convert_error_map_to_string(data):
    if isinstance(data, str):
        return str(data)
    if isinstance(data, unicode):
        return data
    elif isinstance(data, collections.Mapping):
        return dict(map(convert_error_map_to_string, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert_error_map_to_string, data))
    else:
        return data
