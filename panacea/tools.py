# coding: utf-8
from django.conf import settings
import logging

from panacea import exceptions


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

    if not isinstance(name, str):
        raise exceptions.PUsageException('config attribute name must be a string')

    try:
        return getattr(settings, name)
    except:
        try:
            return _globals[name]
        except KeyError:
            if 'default' in kwargs:
                return kwargs.get('default')

    raise exceptions.PConfigException(name)


def get_logger():
    import panacea.config as conf
    return logging.getLogger(conf.get('PCFG_LOGGER_NAME'))
