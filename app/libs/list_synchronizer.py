import logging
from libs.utils.utility import Utility

logger = logging.getLogger(__name__)

class ListSynchronizer():
    def __init__(self, user_repository):
        self._user_repository = user_repository

    def sync(self, not_deleted_entries, deleted_entries):
        sync_list = []
        for key, value in not_deleted_entries.iteritems():
            for item in value:
                if(not self._is_account_enabled(item['ad_data'])):
                    sync_list.append(self._delete_user(item))
                elif not self._user_repository.check_user_exist(Utility.get_first(item['ad_data']['objectGUID'])):
                    sync_list.append(self._add_user(item))
                else:
                    sync_list.append(self._update_user(item))
        for key, value in deleted_entries.iteritems():
            for item in value:
                sync_list.append(self._delete_user(item))
        return sync_list

    def _is_account_enabled(self, ad_data):
        # check if byte 1 is set
        DISABLED_ACCOUNT_BIT = 0x1 << 1
        try:
            return not (int(Utility.get_first(ad_data['userAccountControl'])) & DISABLED_ACCOUNT_BIT) != 0
        except :
            logger.exception("Failed to check if the user is disabled" )
            logger.debug("User information: %s" % ad_data)
            raise

    def _delete_user(self, item):
        item['function'] = self._user_repository.delete_user
        item['description'] = 'Remove user'
        return item

    def _add_user(self, item):
        item['function'] = self._user_repository.add_user
        item['description'] = 'Add user'
        return item

    def _update_user(self, item):
        item['function'] = self._user_repository.update_user
        item['description'] = 'Update user'
        return item
