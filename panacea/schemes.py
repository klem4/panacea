# coding: utf-8
from panacea import config as conf
from panacea import tools

logger = tools.get_logger()


class CacheConf(object):
    """
    класс, описывающий информацию о том,
    как надо кешировать модель, связанную с данным конфигом
    """
    def __init__(self, cache_conf):
        self.cache_conf = cache_conf

    @property
    def ttl(self):
        pass

    @property
    def model(self):
        pass

    @property
    def _dnf(self):
        pass

    def get_cachedas_queryset(self):
        pass


class CacheScheme(object):
    u"""
    класс предоставляющий методы работы со схемами кеширования
    """

    # для удобства и сокращения копипаста созданим ссылку
    # не часть конфига, отвечающую за схемы кеширвоания
    cache_conf = conf.get('PCFG_CACHING')

    def __init__(self, alias):
        self.__alias = alias

    @property
    def scheme(self):
        """
        базовое свойство - схема кеширования
        """
        return self.cache_conf['schemes'][self.__alias]

    @property
    def enabled(self):
        """
        активна ли данная конфигурация кеширования
        по умолчанию - да
        """
        return self.scheme.get("enabled", True)

    @property
    def model_confs(self):
        """
        список конфигов кеширования моделей,
        которые связанны с данной схемой
        """
        return self.scheme.get("models", [])

    @property
    def key_defaults_order(self):
        return self.cache_conf.get("key_defaults_order")


    @classmethod
    def filter(cls, **lookup):
        """
        ищет конфигурацию кеширования
        в конфиге, в случае успеха, инстанцирует и возвращает
        объект класса CacheScheme
        """
        key, value = lookup.popitem()
        if key == 'alias':
            alias = value
        else:
            filter_name = "filter_by_%s" % key

            _filter = getattr(cls, filter_name)
            alias = _filter(value)

        if alias is not None and isinstance(cls.cache_conf['schemes'].get(alias), dict):
            return cls(alias)

    @classmethod
    def filter_by_request(cls, request):
        """
        поиск конфигурации кеширования
        по объекту django.http.HttpRequest или его наследнику
        """
        # получим алиас urlconf по урлу
        urlconf = tools.resolve_path(request)
        if urlconf:
            return urlconf.url_name


    def generate_store_key(self, request):
        """
        получить ключ, соответствующий данной схеме,
        по которому будет закеширован
        контент ответа от api,
        """

        # получим структуру ключа
        key_structure = self.generate_key_structure()
        key_parts = self.generate_key_parts(request)

        return key_structure.format(**key_parts)

    def generate_key_structure(self):
        u"""
        полный формат ключа, по умолчанию
        prefix}{path}{querystring_args}{headers}{cookies}
        """
        separator = conf.get("PCFG_PART_SEPARATOR")
        return "{prefix}{path}%s%s" % (
                separator,
                separator.join(
                "{%s}" % part for part in self.key_defaults_order
            )
        )

    def generate_key_parts(self, request):
        """
        возвращает словарь со сформированными частями
        ключа
        """
        key_parts = {
            'prefix': conf.get('PCFG_KEY_PREFIX'),
            'path': request.path,
        }

        for part in self.key_defaults_order:
            key_parts[part] = getattr(
                self, '_generate_part_%s' % part.lower())(request)

        return key_parts

    def _generate_part_get(self, request):
        u"""
        сформируем часть ключа, основанную на параметрах
        query_string
        """
        return self._get_part('GET', request)

    def _generate_part_meta(self, request):
        u"""
        сформируем часть ключа, основанную на параметрах
        headers
        """
        return self._get_part('META', request)


    def _generate_part_cookies(self, request):
        u"""
        сформируем часть ключа, основанную на параметрах
        cookies
        """
        return self._get_part('COOKIES', request)


    def get_part_keys(self, part_type):
        """
        кастомные ключи уситывающиеся при
        составлении части ключа part_type
        """
        return self.scheme.get(part_type, [])

    def _get_part(self, part_type, request):
        data_dict = getattr(request, part_type)
        separator = conf.get('PCFG_VALUES_SEPARATOR')

        # cначала идут дефолтные значения, затем
        # кастомные для данной схемы

        keys = self.cache_conf['key_defaults'].get(part_type, []) + \
            self.get_part_keys(part_type)

        return separator.join(
            "%s=%s" % (key, data_dict.get(key, '')) for key in keys
        )
