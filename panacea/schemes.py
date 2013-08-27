# coding: utf-8
from django.contrib.contenttypes.models import ContentType

from cacheops.utils import dnf

from panacea import config as conf
from panacea import tools

logger = tools.get_logger()


class CacheConf(object):
    """
    класс, описывающий информацию о том,
    как надо кешировать модель, связанную с данным конфигом
    """
    def __init__(self, model_conf, urlconf):
        self.model_conf = model_conf
        self.urlconf = urlconf
        self.__model = None

    @property
    def model(self):
        if not self.__model:
            (app_label, model) = self.model_conf['model'].split('.')
            self.__model =  ContentType.objects.get(
                    app_label=app_label, model=model
                ).model_class()
        return self.__model

    @property
    def queryset_conditions(self):
        return self.model_conf.get('queryset_conditions', {})

    @property
    def _dnf(self):
        qs = self.get_cached_queryset()
        return dnf(qs)

    def get_cached_queryset(self):
        qs = self.model.objects.all()
        filter_cond = {}
        for model_field, lookup_field in self.queryset_conditions.items():
            filter_cond[model_field] = self.urlconf.kwargs[lookup_field]

        if filter_cond:
            qs = qs.filter(**filter_cond)
        return qs

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
    def alias(self):
        return self.__alias

    @property
    def scheme(self):
        """
        базовое свойство - схема кеширования
        """
        return self.cache_conf['schemes'][self.alias]

    @property
    def enabled(self):
        """
        активна ли данная конфигурация кеширования
        по умолчанию - да
        """
        return self.scheme.get("enabled", True)

    @property
    def ttl(self):
        return int(self.cache_conf.get(
            'ttl',
            conf.get('PCFG_DEFAULT_TTL')
        ))

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

    @classmethod
    def all(cls):
        u"""
        возвращает все имющиеся в конфиге схемы кешироваия
        отсортированный по имени алиаса
        """
        return sorted([
            cls.filter(alias=alias)
            for alias in cls.cache_conf.get('schemes', {}).keys()
        ], cmp=lambda a, b: cmp(a.alias, b.alias))

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


    @classmethod
    def get_default_part_keys(cls, part_type):
        """
        дефолтные ключи учитывающиеся при
        составлении части ключа part_type
        """
        return cls.cache_conf['key_defaults'].get(part_type, [])

    def get_part_keys(self, part_type):
        """
        кастомные ключи учитывающиеся при
        составлении части ключа part_type
        """
        return self.scheme.get(part_type, [])

    def get_all_part_keys(self, part_type):
        """
        все(кастомные+дефолтные) ключи учитывающиеся при
        составлении части ключа part_type
        """
        return self.get_default_part_keys(part_type) + \
            self.get_part_keys(part_type)

    def _get_part(self, part_type, request):
        data_dict = getattr(request, part_type)
        separator = conf.get('PCFG_VALUES_SEPARATOR')

        # cначала идут дефолтные значения, затем
        # кастомные для данной схемы

        keys = self.get_all_part_keys(part_type)

        return separator.join(
            "%s=%s" % (key, data_dict.get(key, '')) for key in keys
        )
