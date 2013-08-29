# coding: utf-8
from StringIO import StringIO
from mock import patch, Mock

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.utils import simplejson
from django.utils.unittest import skipIf
from django.conf import settings

from test_project.test_app import models
from panacea import config as conf
from panacea.invalidation import (
    invalidate_all, invalidate_alias, invalidate_model)

from redis import Redis

class BaseTestCaseMixin(object):
    def setUp(self):
        self.redis = Redis(**settings.CACHEOPS_REDIS)
        self.promo1 = models.Promo.objects.create(name='promo1')
        self.promo2 = models.Promo.objects.create(name='promo2')
        self.redis.flushdb()

    def tearDown(self):
        pass

    def load(self, response):
        return simplejson.loads(response.content)


class CacheConfTestCase(BaseTestCaseMixin, TestCase):
    """
    проверяем работоспособность класса CacheConf
    """
    @skipIf(True, "NOT IMPLEMENTED")
    def testMe(self):
        pass


class ApiSmokeTestCases(BaseTestCaseMixin, TestCase):
    """
    смоковые тесты апишек тестового приложения
    """

    def test_promo_single_smoke(self):
        response = self.client.get(
            reverse('api_promo_single_empty_scheme', args=(self.promo1.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.load(response),
            {'id': self.promo1.id, 'name': self.promo1.name, 'age': None}
        )


    def test_promo_list_smoke(self):
        self.assertEqual(self.client.get(
            reverse('api_promo_list'),
        ).status_code, 200)


class TestAllowCachingMethods(BaseTestCaseMixin, TestCase):
    """
    класс тестирования метода принимающего решение
    о необходимости кеширования ответа от апи

    технически - проверяем, вызывается ли метод store_caching
    в различных условиях
    """
    def setUp(self):
        super(TestAllowCachingMethods, self).setUp()
        self.url1 = reverse('api_promo_single_empty_scheme', args=(self.promo1.pk,))
        self.url1_no_cache = reverse(
            'api_promo_single_not_in_cache',
            args=(self.promo1.pk,)
        )

    @patch('panacea.engine.CacheEngine.process_caching')
    def testAllPass(self, patched_store):
        """
        по дефолту данный запрос проходит все проверки
        """

        r = self.client.get(self.url1)
        self.assertTrue(patched_store.called)
        self.assertEqual(r.status_code, 200)

    @patch('panacea.engine.CacheEngine.process_caching')
    def testWrongMethod(self, patched_store):
        """
            проверяем, что не кешируем ответы
            в случае запроов неверным методом
            по факту - кешируем только get-запросы
        """

        known_methods = ('post', 'put', 'delete')
        for method in known_methods:
            _method = getattr(self.client, method)
            _method(self.url1)
            self.assertFalse(patched_store.called)

    @patch('panacea.engine.CacheEngine.process_caching')
    @patch('django.http.HttpResponse.status_code')
    def testWrongStatusCode(self, patched_response, patched_store):
        """
        проверяем, что не кешируем ответы
        в случае неверного кода ответа api
        """

        known_status_codes = sorted(conf.get('PCFG_ALLOWED_STATUS_CODES'))

        some_bad_code = known_status_codes[-1] + 1

        patched_response.__get__ = Mock(return_value=some_bad_code)
        patched_response.__set__ = Mock()

        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, some_bad_code)
        self.assertFalse(patched_store.called)

        for status in known_status_codes:
             patched_response.__get__ = Mock(return_value=status)
             r = self.client.get(self.url1)
             self.assertEqual(r.status_code, status)
             self.assertTrue(patched_store.called)

    @patch('panacea.engine.CacheEngine.process_caching')
    def testContentType(self, patched_store):
        """
        проверим, что сохраняются только данные заданного формата
        в тестовом приложении мы сохраняем только application/json
        """
        url = self.url1 + '?format=xml'
        r = self.client.get(url)
        self.assertFalse(patched_store.called)
        self.assertEqual(r.status_code, 200)

    @patch('panacea.engine.CacheEngine.process_caching')
    def testScheme(self, patched_store):
        """
        данный url отсутствует в схеме кеширования
        """
        r = self.client.get(self.url1_no_cache)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

    @patch('panacea.engine.CacheEngine.process_caching')
    def testLocalDisabled(self, patched_store):
        from django.conf import settings
        settings.PCFG_CACHING['schemes']['api_promo_single_empty_scheme']['enabled'] = False

        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

        settings.PCFG_CACHING['schemes']['api_promo_single_empty_scheme']['enabled'] = True

    @patch('panacea.engine.CacheEngine.process_caching')
    def testGlobalDisabled(self, patched_store):
        from django.conf import settings
        settings.PCFG_ENABLED = False

        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

        settings.PCFG_ENABLED = True


class TestGenerateKey(BaseTestCaseMixin, TestCase):
    u"""
    тестируем функцию геренации ключа,
    по которому произойдет сохранение ответа от api
    построение ключа, зависит от схемы кеширования,
    которая указана для урла api
    """
    def setUp(self):
        super(TestGenerateKey, self).setUp()

        self.cases = [
            # второй кейс, в составлении ключа учавствуют только дефолтные параметры
            # большинство из них пустые, но они всеравно всегда присутствуют
            # в ключе
            (
                reverse(
                    'api_promo_single_test_key_second',
                    args=(self.promo1.id,)
                ),
                'panacea:/api/promo/single/%s/second;'
                'default_qs1=' % self.promo1.id
            )
        ]


    @patch('panacea.engine.CacheEngine.store_schemes')
    def testAllPartsEmpty(self, store_schemes):
        u"""в составлении ключа
        не учавствуют никакие параетры
        """
        url = reverse(
            'api_promo_single_test_key_first',
            args=(self.promo1.id,)
        )

        key = 'panacea:api_promo_single_test_key_first' \
              ':/api/promo/single/%s/first;;;' % self.promo1.id

        old = settings.PCFG_CACHING['key_defaults']
        settings.PCFG_CACHING['key_defaults'] = {
            'GET': [],
            'META': [],
            'COOKIES': []
        }

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)

        settings.PCFG_CACHING['key_defaults'] = old

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testOnlyDefaults1(self, store_schemes):
        u"""в составлении ключа
        не учавствуют только дефолтные параметры
        """
        url = reverse(
            'api_promo_single_test_key_second',
            args=(self.promo1.id,)
        ) + '?default_qs1=value1&default_qs2=value2'

        key = 'panacea:api_promo_single_test_key_second' \
              ':/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' \
              'some_cookie1=&some_cookie2=' % self.promo1.id

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testOnlyDefaults2(self, store_schemes):
        u"""
        то же самое, что и предыдущий кейс,
        но параметры в запросе идут в другом порядку
        """

        url = reverse(
            'api_promo_single_test_key_second',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1'

        key = 'panacea:api_promo_single_test_key_second' \
              ':/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' \
              'some_cookie1=&some_cookie2=' % self.promo1.id

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testUnknownQsArgs(self, store_schemes):
        """
        добавляем к преыдущему варианту неизвестные
        для схемы параметры, они не дают никакого эффекта
        """
        url = reverse(
            'api_promo_single_test_key_second',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1&x=1&y=2'

        key = 'panacea:api_promo_single_test_key_second' \
              ':/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' \
              'some_cookie1=&some_cookie2=' % self.promo1.id

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testNonEmptyHeaders(self, store_schemes):
        """
        добавляем к преыдущему варианту непустые заголовки
        """
        url = reverse(
            'api_promo_single_test_key_second',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1&x=1&y=2'

        key = 'panacea:api_promo_single_test_key_second' \
              ':/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=some/user/agent&HTTP_ACCEPT_ENCODING=some/encoding;' \
              'some_cookie1=&some_cookie2=' % self.promo1.id

        r = self.client.get(url, **{
            'HTTP_USER_AGENT': 'some/user/agent',
            'HTTP_ACCEPT_ENCODING': 'some/encoding'
        })

        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testNonEmptyCookies(self, store_schemes):
        """
        добавляем к преыдущему варианту непустые куки
        """
        url = reverse(
            'api_promo_single_test_key_second',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1&x=1&y=2'

        key = 'panacea:api_promo_single_test_key_second:/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=some/user/agent&HTTP_ACCEPT_ENCODING=some/encoding;' \
              'some_cookie1=cookie_value1&some_cookie2=cookie_value2' % self.promo1.id

        self.client.cookies['some_cookie1'] = 'cookie_value1'
        self.client.cookies['some_cookie2'] = 'cookie_value2'


        r = self.client.get(url, **{
            'HTTP_USER_AGENT': 'some/user/agent',
            'HTTP_ACCEPT_ENCODING': 'some/encoding'
        })

        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testEmptyCustomValues(self, store_schemes):
        """
        тут испльзуем другую схему кешироваия, в ней учитываются
        кастомные параметры qs, cookie, header,  но все они пустые
        """
        url = reverse(
            'api_promo_single_test_key_third',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1&x=1&y=2&custom_qs1=xxx'

        key = 'panacea:api_promo_single_test_key_third' \
              ':/api/promo/single/%s/third;' \
              'default_qs1=value1&default_qs2=value2&custom_qs1=xxx;' \
              'HTTP_USER_AGENT=some/user/agent&HTTP_ACCEPT_ENCODING=some/encoding' \
              '&HTTP_CUSTOM_META=custom_meta_value;' \
              'some_cookie1=cookie_value1&some_cookie2=cookie_value2' \
              '&custom_cookie=yyy' % self.promo1.id

        self.client.cookies['some_cookie1'] = 'cookie_value1'
        self.client.cookies['some_cookie2'] = 'cookie_value2'
        self.client.cookies['custom_cookie'] = 'yyy'



        r = self.client.get(url, **{
            'HTTP_USER_AGENT': 'some/user/agent',
            'HTTP_ACCEPT_ENCODING': 'some/encoding',
            'HTTP_CUSTOM_META': 'custom_meta_value'
        })

        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)

    @patch('panacea.engine.CacheEngine.store_schemes')
    def testNonEmptyCustomValues(self, store_schemes):
        """
        аналогично предыдущему тесты, но все кастомные значения заданы
        """
        url = reverse(
            'api_promo_single_test_key_third',
            args=(self.promo1.id,)
        ) + '?default_qs2=value2&default_qs1=value1&x=1&y=2'

        key = 'panacea:api_promo_single_test_key_third' \
              ':/api/promo/single/%s/third;' \
              'default_qs1=value1&default_qs2=value2&custom_qs1=;' \
              'HTTP_USER_AGENT=some/user/agent&HTTP_ACCEPT_ENCODING=some/encoding' \
              '&HTTP_CUSTOM_META=;' \
              'some_cookie1=cookie_value1&some_cookie2=cookie_value2' \
              '&custom_cookie=' % self.promo1.id

        self.client.cookies['some_cookie1'] = 'cookie_value1'
        self.client.cookies['some_cookie2'] = 'cookie_value2'


        r = self.client.get(url, **{
            'HTTP_USER_AGENT': 'some/user/agent',
            'HTTP_ACCEPT_ENCODING': 'some/encoding'
        })

        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)


class TestCaching(BaseTestCaseMixin, TestCase):
    """
    тестируем правильность сохранения данных в редис
    """
    @patch('panacea.tools.cache_thing')
    def test1(self, patched_cache_thing):
        """
        тут проверяем, что cached_as вызывается с правильными
        параметрами
        """
        url = reverse('api_promo_single_cache1',
                      args=(self.promo1.id,))

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        self.assertTrue(patched_cache_thing.called)
        _model = models.Promo
        _key = 'panacea:api_promo_single_cache1' \
               ':/api/promo/single/%s/cache1;default_qs1=&default_qs2=&custom_qs1=;' \
               'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=&HTTP_CUSTOM_META=;' \
               'some_cookie1=&some_cookie2=&custom_cookie=' % self.promo1.id

        _content = '{"id": %s, "name": "promo1", "age": null}' % self.promo1.id
        _ttl = 600
        _dnf = [[('id', self.promo1.id)]]

        patched_cache_thing.assert_called_with(
            _model,
            _key,
            _content,
            _dnf,
            _ttl
        )

    def test2(self):
        """
        тут проверяем, что ключ сохраняется в правильной схеме,
        а также что врено сохраняется контент
        """
        url = reverse('api_promo_single_cache1',
                      args=(self.promo1.id,))

        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)

        _key = 'panacea:api_promo_single_cache1' \
               ':/api/promo/single/%s/cache1;default_qs1=&default_qs2=&custom_qs1=;' \
               'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=&HTTP_CUSTOM_META=;' \
               'some_cookie1=&some_cookie2=&custom_cookie=' % self.promo1.id

        _content = '{"id": %s, "name": "promo1", "age": null}' % self.promo1.id
        _ttl = 600

        self.assertEqual(len(self.redis.keys('*')), 7)
        self.assertEqual(self.redis.get(_key), _content)

        self.assertIn(_key, self.redis.keys('*'))
        self.assertIn(_key, self.redis.smembers(
            'conj:test_app.promo:id=%s' % self.promo1.id)
        )

    def test3(self):
        """
        тестируем кеширование схемы, в которой
        одна модель присутствует дважды, и ключ сохраняется
        в две разные схемы cacheops
        """
        age = 1
        url = reverse('api_promo_single_cache2',
                      args=(self.promo1.id, age))

        self.client.get(url)

        key1 = "panacea:api_promo_single_cache2" \
               ":/api/promo/single/%s/%s/cache2;" \
               "default_qs1=&default_qs2=;" \
               "HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;" \
               "some_cookie1=&some_cookie2=" % (
                    self.promo1.id, age
                )

        self.assertIn(key1, self.redis.keys('*'))

        self.assertIn(key1, self.redis.smembers(
            "conj:test_app.promo:id=%s" % self.promo1.id))

        self.assertIn(key1, self.redis.smembers(
            "conj:test_app.promo:age=%s&id=%s" % (age, self.promo1.id)))

        self.assertTrue(len(self.redis.keys('panacea*')) == 1)


    def test4(self):
        """
        тестируем кеширование схемы  с составным
        lookup полем
        """
        url = reverse('api_promo_single_cache3',
                      args=(self.promo1.id,))

        self.client.get(url)

        _key = "panacea:api_promo_single_cache3" \
               ":/api/promo/single/%s/cache3;default_qs1=&default_qs2=;" \
               "HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;" \
               "some_cookie1=&some_cookie2=" % self.promo1.id

        self.assertIn(_key, self.redis.keys('*'))

        self.assertIn(_key, self.redis.smembers(
             'conj:test_app.promoarea:promo_id=%s' % self.promo1.id))


class NginxConfCmdTestCase(BaseTestCaseMixin, TestCase):
    u"""
    теутсруем комманду генерации конфига nginx
    сравниваем то что генерит команда, с заранее сохраненным эталоном
    """
    def testConfigNotChanged(self):
        stdout = StringIO()
        call_command('nginx_cache_conf', stdout=stdout)
        stdout.seek(0)

        cmd_output = "".join([line for line in stdout.readlines()])
        config = open("test_project/test_project/test_app/tests_nginx_conf.txt", "r").read()

        self.assertEqual(cmd_output, config)


class InvalidationTestCase(BaseTestCaseMixin, TestCase):
    all_panacea_keys = '%s*' % conf.get('PCFG_KEY_PREFIX')

    def setUp(self):
        super(InvalidationTestCase, self).setUp()
        self.urls = [
            reverse('api_promo_single_cache3',
                      args=(self.promo1.id,)),
            reverse('api_promo_single_cache2',
                      args=(self.promo1.id, 1)),
            reverse('api_promo_single_cache1',
                      args=(self.promo1.id,)),
            reverse('api_promo_single_cache1',
                      args=(self.promo2.id,))
        ]

        self.assertEqual(self.redis.keys(self.all_panacea_keys), [])

        for url in self.urls:
            self.client.get(url)

        self.total_keys_cnt = len(self.redis.keys(self.all_panacea_keys))

        self.assertEqual(
            len(self.redis.keys(self.all_panacea_keys)), len(self.urls)
        )

    def testInvalidateAll(self):
        invalidate_all()

        self.assertEqual(
            len(self.redis.keys(self.all_panacea_keys)), 0
        )

        self.assertEqual(
            len(self.redis.keys(self.all_panacea_keys)), self.total_keys_cnt - len(self.urls)
        )

    def testInvalidateAliases(self):
        self.assertEqual(
            len(self.redis.keys('panacea:api_promo_single_cache1*')), 2)

        invalidate_alias('api_promo_single_cache1')
        self.assertFalse(self.redis.keys('panacea:api_promo_single_cache1*'))
        self.assertTrue(self.redis.keys(self.all_panacea_keys))
        self.assertEqual(
            len(self.redis.keys(self.all_panacea_keys)), self.total_keys_cnt - 2
        )

    def testInvalidateModels(self):
        self.assertTrue(self.redis.keys('panacea:api_promo_single_cache3*'))
        invalidate_model('test_app.PromoArea')
        self.assertFalse(self.redis.keys('panacea:api_promo_single_cache3*'))
        self.assertEqual(
            len(self.redis.keys(self.all_panacea_keys)), self.total_keys_cnt - 1
        )
