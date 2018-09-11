class DistinguishedNameExtractor:
    # extract name of DN/OU in string like OU=Users,DC=example,DC=com
    def extract_group_name(self, dn):
        parts = dn.split(',')
        if(len(parts) < 2):
            raise DistinguishedNameExtractionException("Not enough parts in disinguished name %s" % parts)
        value_parts = parts[1].split('=')
        if(len(value_parts) < 2):
            raise DistinguishedNameExtractionException("No value after equals in distinguished name part %s" % value_parts)
        return value_parts[1]


class DistinguishedNameExtractionException(Exception):
    pass
