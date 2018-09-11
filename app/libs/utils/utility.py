#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import logging
import unicodedata

logger = logging.getLogger(__name__)

try:
    import json
    import yaml
except Exception, e:
    logger.exception(e)


class Utility(object):

    #In : encoded json (json_object)
    #Out : decoded json
    @classmethod
    def decode_json(cls, json_object):
        json_decoder = json.JSONDecoder(object_hook=cls._convert_to_string)
        return json_decoder.decode(json_object)

    #In : decoded json (json_object)
    #Out : encoded json
    @classmethod
    def encode_json(cls, data):
        json_encoder = json.JSONEncoder(encoding='utf-8', ensure_ascii=True)
        return json_encoder.encode(data)

    @classmethod
    def strip_accents(cls, s):
        if isinstance(s, str):
            s = s.decode('utf-8')
        return ''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))

    #In : string (data)
    #Out : string (converted_data)
    @classmethod
    def _convert_to_string(cls, data):
        converted_data = {}
        if(isinstance(data, unicode)):
            return str(cls.strip_accents(data))
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            if isinstance(value, unicode):
                value = value.encode('utf-8')
            if isinstance(value, list):
                value = map(lambda s: cls._convert_to_string(s), value)
            converted_data[key] = value
        return converted_data

    #In : string (file_path)
    #Out : dict (dataDict)
    @classmethod
    def parse_yaml(cls, file_path):
        f = open(file_path)
        dataDict = yaml.load(f)
        f.close()
        return dataDict

    #In : function (func)
    #Out : None
    @classmethod
    def permissive_execute(cls, func, *args):
        try:
            func(*args)
        except Exception, e:
            logger.exception(e)
            return False
        return True

    #In : dict or list (iterable)
    #Out : object (first or default)
    @classmethod
    def get_first(cls, iterable, default=None):
        if iterable:
            for item in iterable:
                return item
        return default

    @classmethod
    def verify_contain_keys(cls, iterable, keys):
        for k in keys:
            if not k in iterable:
                return False
        return True

    @classmethod
    def remove_keys(cls, iterable, keys):
        for k in keys:
            try:
                del(iterable[k])
            except:
                continue

    class UnRetryableException(Exception):
        pass
