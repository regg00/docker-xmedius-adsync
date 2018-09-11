import fnmatch
import logging

logger = logging.getLogger(__name__)


class LdapExclusionFilter():
    def __init__(self, query_params):
        self.query_params = query_params

    def filter(self, results):
        if(not 'exclusion' in self.query_params):
            return results

        def exclude_mails(result):
            data = result[1]
            for attribute in self.query_params['exclusion']:
                for exclusion in self.query_params['exclusion'][attribute]:
                    if(self._is_attribute_excluded(data, attribute, exclusion)):
                        return False
            return True
        return filter(exclude_mails, results)

    def _is_attribute_excluded(self, data, attribute, exclusion):
        if attribute in data:
            for value in data[attribute]:
                if(fnmatch.fnmatch(value, exclusion)):
                    logger.info("Ignoring entry %s, exclusion=%s, value=%s for attribute=%s" % (data['uSNChanged'], exclusion, value, attribute))
                    return True
        return False
