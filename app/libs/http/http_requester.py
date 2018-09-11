#////////////////////////////////////////////////////////////////////////////
# Copyright (c) 2012 Sagemcom Canada Permission to use this work
# for any purpose must be obtained in writing from Sagemcom Canada
# 5252 de Maisonneuve Blvd. West, suite 400, Montreal, Quebec H4A 3S5
#////////////////////////////////////////////////////////////////////////////

import logging

logger = logging.getLogger(__name__)

try:
    import urllib2
except Exception, e:
    logging.exception("Failed to import urllib2")
    raise


class HTTPRequester:

    def __init__(self, address, authorization):
        self._address = address
        self._authorization_token = authorization

    def _request(self, method, url, params_content):
        reformed_url = '%s/%s' % (self._address, url)
        logger.info("Http request %s %s" % (method, reformed_url))
        try:
            request = urllib2.Request(reformed_url, params_content)
            request.add_header('authorization-token', self._authorization_token)
            request.add_header('Content-type', "application/json")
            request.add_header('Accept', "application/json")
            request.get_method = lambda: method
            response = urllib2.urlopen(request)
            return response.read()
        except Exception, e:
            raise Exception('Request %s %s. Error : %s.' % (method, reformed_url, str(e)))

    def post(self, url, params_content=''):
        return self._request("POST", url, params_content)

    def put(self, url, params_content=''):
        return self._request("PUT", url, params_content)

    def get(self, url, params_content=''):
        return self._request("GET", url, params_content)

    def delete(self, url, params_content=''):
        return self._request("DELETE", url, params_content)
