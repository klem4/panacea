# coding: utf-8

from mock import patch, Mock
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.conf import settings

from test_project.test_app import models
from panacea import config as conf



class BaseTestCaseMixin(object):
    def setUp(self):
        self.promo1 = models.Promo.objects.create(name='promo1')
        self.promo2 = models.Promo.objects.create(name='promo2')

    def tearDown(self):
        pass

    def load(self, response):
        return simplejson.loads(response.content)


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
            {'id': self.promo1.id, 'name': self.promo1.name}
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

        key = 'panacea:/api/promo/single/%s/first;;;' % self.promo1.id

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

        key = 'panacea:/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' % self.promo1.id

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

        key = 'panacea:/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' % self.promo1.id

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

        key = 'panacea:/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=&HTTP_ACCEPT_ENCODING=;' % self.promo1.id

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

        key = 'panacea:/api/promo/single/%s/second;default_qs1=value1&default_qs2=value2;' \
              'HTTP_USER_AGENT=some/user/agent&HTTP_ACCEPT_ENCODING=some/encoding;' % self.promo1.id

        r = self.client.get(url, **{
            'HTTP_USER_AGENT': 'some/user/agent',
            'HTTP_ACCEPT_ENCODING': 'some/encoding'
        })

        self.assertEqual(r.status_code, 200)

        store_schemes.assert_called_with(key)
