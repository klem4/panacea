# coding: utf-8

class PExceptionTraceBackMixin(object):
    """
    Миксин для классов исключений расширяющий
    сообщение об ошибке стек-трейсом
    """
    pass


class PBaseException(Exception):
    """
    Базовый класс исключений
    """
    pass


class PUsageException(PExceptionTraceBackMixin, PBaseException):
    """
    Ошибка: некорреткная работа с кодом(передано недостаточно аргументов,
    не найдена функция по имени и проч.)
    """
    pass


class PConfigException(PExceptionTraceBackMixin, PBaseException):
    """
    Ошибка: отсутсвтие параметра в конфиге, или дефолтного значения
    при его отсутствии
    """
    pass