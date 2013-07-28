# coding: utf-8

import panacea.config as conf
from panacea.tools import get_logger

logger = get_logger()

class CacheEngine(object):
    u"""
    движок кеширующего механизма
    """

    def __init__(self, request, response, rest_wrappers):
        # напрямую работа с объектами request и response
        # вестись не должна, для доступа к аттрибутам объектов
        # используются обертки на основе rest_frameworks
        self.__request = request
        self.__response = response
        self.__wrappers = map(
            lambda WrapperClass: WrapperClass(request, response),
            rest_wrappers
        )

    def store_cache(self):
        pass

    def allow_caching(self):
        for checker_name in ('method', 'status_code', 'content_type', 'scheme'):
            method_name = 'chk_%s' % checker_name
            if hasattr(self, method_name):
                checker_method = getattr(self, 'chk_%s' % checker_name)
                if checker_method and not checker_method():
                    return
            else:
                logger.error("handler not found: %s" % method_name)
                return False
        return True

    def chk_method(self):
        """
        кешируем только GET-запросы
        """
        return self.request_method == 'GET'

    def chk_status_code(self):
        """
        кешируем только ответы с определенынми статусами
        """
        return self.response_status_code in conf.get('PSHM_ALLOWED_STATUS_CODES')

    def chk_content_type(self):
        """
        кешируем только ответы определенного типа
        """
        return self.response_content_type == conf.get('PSHM_ALLOWED_CONTENT_TYPE')

    def chk_scheme(self):
        return False

    @property
    def request_method(self):
        u""" тип запроса: GET, POST, DELETE, ... """
        return self.__get_attr('method')

    @property
    def response_content_type(self):
        u"""тип запрашиваемого клиентом контента:
             application/json, text/plain ... """
        return self.__get_attr('content_type')

    @property
    def response_status_code(self):
        u"""
        код ответа: 200, 404, ...
        """
        return self.__get_attr('status_code')

    def __get_attr(self, attr_name):
        u"""
        пытаемся отыскать вариант обертки над объектами
        request и response, возволяющий получить значение
        аттрибута
        """
        for wrapper in self.__wrappers:
            try:
                return getattr(wrapper, attr_name)
            except Exception as e:
                continue
