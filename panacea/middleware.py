# coding: utf-8

from panacea.engine import CacheEngine
from panacea.tools import get_logger

logger = get_logger()


class NginxRedisCachingMiddleware(object):
    u"""
    кеширующий middleware
    в случае прохождения проверки, сохраняет
    контент ответа в redis средствами cacheops для
    полсдедующей возожной отдачи непосредственно nginx'ом
    по средствам модуля httpredis
    """

    def process_response(self, request, response):
        #import pdb; pdb.set_trace()
        engine = CacheEngine(request, response)
        if engine.allow_caching():
            engine.process_caching()
        return response