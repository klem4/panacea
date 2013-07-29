# coding: utf-8

u"""
Конфигурационный файл приложения.

Работа с параметрами должна осуществляться по средствами вызовов
функций config.get(var_name)

Метод get реализован таким образом, что имеет приоритет на значения
из settings.py, таким образом все переменные, описанные в понфиге
могут быть переопределены
"""

from panacea.tools import _get
get = lambda name: _get(globals(), name)

__all__ = ['get']


# префикс ключей в redis
PCFG_KEY_PREFIX = 'panacea.'

# имя логгера по умолчанию
# если значение на задать, будет использован
# дефолтный логгер root
PCFG_LOGGER_NAME = None

# допустимые коды ответов для кеширвоания
PCFG_ALLOWED_STATUS_CODES = (200,)

# будут кешироваться только ответы данного ct
PCFG_ALLOWED_CONTENT_TYPE = 'application/json'


PCFG_SHEMES = {
    'schemes': {}
}