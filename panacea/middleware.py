# coding: utf-8

from panacea.engine import CacheEngine
from panacea import rest_wrappers
from panacea.tools import get_logger

logger = get_logger()


class NginxRedisCachingMiddleware(object):
    u"""
    кеширующий middleware
    в случае прохождения проверки, сохраняет
    контент ответа в redis средствами cacheops для
    полсдедующей возожной отдачи непосредственно nginx'ом
    по средствам подуля httpredis
    """

    # различные версии rest-фреймворков поставляют в качестве
    # request и response объекты различных типов в методы
    # process_response и process_request миддлвейра,
    # в данном списке необходиом указывать известные обработчикии
    # данных объектов
    # допускается переопределение данного параметра
    # при переопределении класса middleware

    rest_frameworks = (
        # умеем работать в объектами django-rest-framework версий 2.x
        rest_wrappers.DjangoRestFramework2x,
        # умеем работать в объектами django-rest-framework версий 0.x
        rest_wrappers.DjangoRestFramework0x,
    )

    def process_response(self, request, response):
        try:
            engine = CacheEngine(request, response, self.rest_frameworks)
            if engine.allow_caching():
                engine.store_cache()
        except Exception as e:
            logger.error(e)

        return response