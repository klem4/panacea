# coding: utf-8

import panacea.config as conf
from panacea.schemes import CacheScheme
from panacea.tools import get_logger

logger = get_logger()


class CacheEngine(object):
    u"""
    движок кеширующего механизма
    """

    def __init__(self, request, response):
        self.request = request
        self.response = response
        self.scheme = None

    def process_caching(self):
        u"""
        кешируем результат выполнения запроса
        в соответствии с указанной схемой
        """

        # получим ключ, по которому будет
        # сохранен контент ответа api
        panacea_key = self.scheme.generate_store_key(self.request)
        logger.debug("process_caching: %s" % panacea_key)

        self.store_schemes(panacea_key)

    def store_schemes(self, key):
        """
        кешируем конткнт ответа от api под ключем key
        по всех схемам, описанных в конфиге для данного урла
        """
        pass

    def allow_caching(self):
        u"""
        проверяем, необходимо ли кешированть
        данный запрос
        """

        # кеширование отключено глобально
        if not conf.get('PCFG_ENABLED', default=False):
            return

        for checker_name in ('method', 'status_code', 'content_type', 'scheme'):
            method_name = 'chk_%s' % checker_name
            if hasattr(self, method_name):
                checker_method = getattr(self, 'chk_%s' % checker_name)
                if not checker_method():
                    return
            else:
                logger.error("handler not found: %s" % method_name)
                return

        return True

    def chk_method(self):
        u"""
        кешируем только GET-запросы
        """
        return self.request.method == 'GET'

    def chk_status_code(self):
        u"""
        кешируем только ответы с определенынми статусами
        """
        return self.response.status_code in conf.get('PCFG_ALLOWED_STATUS_CODES')

    def chk_content_type(self):
        u"""
        кешируем только ответы определенного типа
        """
        return self.response.get('content-type') == conf.get('PCFG_ALLOWED_CONTENT_TYPE')

    def chk_scheme(self):
        """
        метод проверки необходимости кеширования
        данного урла, производит поиск данных
        о кешировании в конфиге, в случае удачи, сохраняет
        вычисленные и необходимые для кеширования промежуточные
        данные и возвращает True
        """
        self.scheme = CacheScheme.filter(request=self.request)
        return self.scheme and self.scheme.enabled
