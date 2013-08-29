# coding: utf-8
from cacheops.invalidation import cache_schemes, conj_cache_key
from cacheops.utils import conj_scheme, non_proxy
from cacheops.conf import model_profile, redis_client

from django.conf import settings
from django.core import urlresolvers

import logging

def resolve_path(request):
    try:
      return urlresolvers.resolve(request.path)
    except urlresolvers.Resolver404:
        pass
    except Exception as e:
        get_logger().error(e)


def cache_thing(model, cache_key, data, cond_dnf=[[]], timeout=None):
    u"""
        По факту - скопированный метод cache_thing из кешопса
            с двумя изменениями:
                - просто функция, а не метод объекта
                - убрана сериализация data с помощью pickle.dumps
    """

    model = non_proxy(model)

    if timeout is None:
        profile = model_profile(model)
        timeout = profile['timeout']

    # Ensure that all schemes of current query are "known"
    schemes = map(conj_scheme, cond_dnf)
    cache_schemes.ensure_known(model, schemes)

    txn = redis_client.pipeline()

    # Write data to cache
    if timeout is not None:
        txn.setex(cache_key, timeout, data)
    else:
        txn.set(cache_key, data)

    # Add new cache_key to list of dependencies for
    # every conjunction in dnf
    for conj in cond_dnf:
        conj_key = conj_cache_key(model, conj)
        txn.sadd(conj_key, cache_key)
        if timeout is not None:
            # Invalidator timeout should be larger than
            # timeout of any key it references
            # So we take timeout from profile which is our upper limit
            # Add few extra seconds to be extra safe
            txn.expire(conj_key, model._cacheprofile['timeout'] + 10)

    txn.execute()


def _get(_globals, name, **kwargs):
    u"""
    метод для получения значения из конфига
    сначала ищем в settings, если параметра там нет
    то берем из вызываемого файла,
    если и так нет, то exception

    использование в модуле, на примере config.py:

    >>from panacea.tools import _get
    >>get = lambda name, **kwargs: _get(globals(), name, **kwargs)
    >>__all__ = ['get']

    далее после импорта config в любом месте:
    >>import config as conf
    >>conf.get('SOME_VARIABLE')
    >>conf.get('SOME_VARIABLE', default={})
    """

    try:
        return getattr(settings, name)
    except:
        try:
            return _globals[name]
        except KeyError:
            if 'default' in kwargs:
                return kwargs.get('default')


def get_aliases_by_models(models):
    from panacea.schemes import CacheScheme
    if not isinstance(models, (list, tuple)):
        models = [models,]

    aliases = []
    for scheme in CacheScheme.all():
        for model_conf in scheme.model_confs:
            if model_conf['model'] in models:
                aliases.append(scheme.alias)
                break
    return aliases


def get_logger():
    import panacea.config as conf
    return logging.getLogger(conf.get('PCFG_LOGGER_NAME'))
