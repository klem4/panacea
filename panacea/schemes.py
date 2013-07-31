# coding: utf-8
from django.core import urlresolvers
from panacea import config as conf
from panacea.tools import get_logger
from panacea import exceptions

logger = get_logger()


class CacheScheme(object):
    cache_conf = conf.get('PCFG_CACHING')

    def __init__(self, scheme):

        if not isinstance(scheme, dict):
            raise exceptions.PUsageException(
                'scheme must be a dictionary, not %s' % type(scheme)
            )

        self.__scheme = scheme

    @property
    def enabled(self):
        """
        активна ли данная конфигурация кеширования
        по умолчанию - да
        """
        return self.__scheme.get("enabled", True)

    @classmethod
    def filter(cls, **lookup):
        """
        ищет конфигурацию кеширования
        в конфиге, в случае успеха, инстанцирует и возвращает
        объект класса CacheScheme
        """

        # можем искать только по одному параметру
        if not len(lookup) == 1:
            raise exceptions.PUsageException(
                'lookup must contains only one argument'
            )

        key, value = lookup.popitem()
        filter_name = "filter_by_%s" % key

        if not hasattr(cls, filter_name):
            raise exceptions.PUsageException(
                'no such filter: %s' % filter_name
            )

        _filter = getattr(cls, filter_name)

        if not callable(_filter):
            raise exceptions.PUsageException(
                'filter %s is not callable' % filter_name
            )

        scheme = _filter(value)

        if scheme:
            return cls(scheme)

    @classmethod
    def filter_by_alias(cls, alias):
        """
        поиск конфигурации кеширования по алиасу
        """
        return cls.cache_conf['schemes'].get(alias) 

    @classmethod
    def filter_by_request(cls, request):
        """
        поиск конфигурации кеширования
        по объекту django.http.HttpRequest или его наследнику
        """
        from django.http import HttpRequest
        if not isinstance(request, HttpRequest):
            raise exceptions.PUsageException(
                'request must be HttpRequest instance'
            )

        # получим алиас urlconf по урлу
        try:
            urlconf = urlresolvers.resolve(request.path)
        except urlresolvers.Resolver404:
            return
        except Exception as e:
            logger.error(e)
            return

        return cls.filter_by_alias(urlconf.url_name)
