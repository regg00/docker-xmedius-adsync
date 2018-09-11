import logging

from libs.http.attributes_modifier import AttributesModifier
from libs.utils.utility import Utility
from libs.http.dn_extractor import DistinguishedNameExtractor
from libs.utils.dict_differ import DictDiffer

logger = logging.getLogger(__name__)


class AttributesMatcher:

    def __init__(self, config_data, default_group_id, assigned_groups, default_fax_id, assigned_faxes):
        self._config_data = config_data
        self._default_group_id = default_group_id
        self._assigned_groups = assigned_groups
        self._default_fax_id = default_fax_id
        self._assigned_faxes = assigned_faxes

    #In : dict (ad_data), dict (attributes)
    #Out : dict (attributes)
    def match_attributes(self, ad_data, attributes):
        if 'attributes_mapping' in self._config_data:
            for key, value in self._config_data['attributes_mapping'].iteritems():
                try:
                    if(self._is_magic_value(value)):
                        dn = Utility.get_first(ad_data['distinguishedName'])
                        attributes[key] = DistinguishedNameExtractor().extract_group_name(dn)
                    else:
                        ad_value = ad_data[value][0]
                        attributes[key] = ad_value
                except KeyError:
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue
            # override values as specified by user
            modified_attributes = AttributesModifier().modify_attributes(attributes.copy())
            changed_keys = DictDiffer(modified_attributes, attributes).all_changes()
            attributes = modified_attributes

            for key, value in self._config_data['attributes_mapping'].iteritems():
                try:
                    key_found = value in ad_data or self._is_magic_value(value) or key in changed_keys
                    if(key_found):
                        if key == 'group_id':
                            attributes[key] = self.match_or_set_default(self._assigned_groups, self._default_group_id, attributes[key])
                        elif key == 'main_fax_number_id':
                            digit_only_fax = '+' + filter(lambda x: x.isdigit(), attributes[key])
                            attributes[key] = self.match_or_set_default(self._assigned_faxes, self._default_fax_id, digit_only_fax, lambda x, y: x['number'].lower() == y.lower())
                        elif key == 'username':
                            attributes[key] = Utility.strip_accents(attributes[key])
                    else:
                        # if 'main_fax_number_id' key is not found, reset attribute
                        if(key == 'main_fax_number_id'):
                            attributes[key] = None
                        if(key == 'group_id'):
                            attributes[key] = self._default_group_id
                except KeyError:
                    continue
                except Exception as e:
                    logger.exception(e)
                    continue
        return attributes

    def _is_magic_value(self, value):
        # if we were to have many magic values, maybe it would be worth it to use
        # hasattr(obj, value) and callable(obj.value) and call the right method dynamically.
        # However we would then force the user to type the exact name (case-sensitive) and
        # weird behaviors could happen if other methods were called.
        return value.lower() == 'ExtractGroupNameFromDn'.lower()

    #In : dict (matched_dict), string (default_value_id), string (compared_value)
    #Out : dict (_users_by_id[id])
    def match_or_set_default(self, matched_dict, default_value_id, compared_value, comparator=lambda x, y: x.lower() == y.lower()):
        results = [k for k, v in matched_dict.iteritems() if comparator(v, compared_value)]
        if results:
            result = Utility.get_first(results)
        else:
            result = default_value_id

        return result
