# coding: utf-8

import panacea.config as conf
from panacea.tools import get_logger

logger = get_logger()

class CacheEngine(object):
    u"""
    движок кеширующего механизма
    """

    def __init__(self, request, response):
        self.request = request
        self.response = response

    def store_cache(self):
        pass

    def allow_caching(self):
        for checker_name in ('method', 'status_code', 'content_type', 'scheme'):
            method_name = 'chk_%s' % checker_name
            if hasattr(self, method_name):
                checker_method = getattr(self, 'chk_%s' % checker_name)
                if not checker_method():
                    return
            else:
                logger.error("handler not found: %s" % method_name)
                return False
        return True

    def chk_method(self):
        """
        кешируем только GET-запросы
        """
        return self.request.method == 'GET'

    def chk_status_code(self):
        """
        кешируем только ответы с определенынми статусами
        """
        return self.response.status_code in conf.get('PSHM_ALLOWED_STATUS_CODES')

    def chk_content_type(self):
        """
        кешируем только ответы определенного типа
        """
        return False

    def chk_scheme(self):
        return False
