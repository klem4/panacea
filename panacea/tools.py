# coding: utf-8
from django.conf import settings
import logging


def _get(_globals, name):
    u"""
    метод для получения значения из конфига
    сначала ищем в settings, если параметра там нет
    то берем из вызываемого файла,
    если и так нет, то exception

    использование в модуле, например config.py:

    >>from panacea.tools import _get
    >>get = lambda name: _get(globals(), name)
    >>__all__ = ['get']

    далее после импорта config в любом месте:
    >>import config as conf
    >>conf.get('SOME_VARIABLE')
    """
    try:
        return getattr(settings, name)
    except:
        return _globals[name]


def get_logger():
    import panacea.config as conf
    return logging.getLogger(conf.get('PCFG_LOGGER_NAME'))
logger = get_logger()
