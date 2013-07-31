# coding: utf-8

from mock import patch, Mock
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson

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
            reverse('api_promo_single', args=(self.promo1.pk,))
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
        self.url1 = reverse('api_promo_single', args=(self.promo1.pk,))
        self.url1_no_cache = reverse(
            'api_promo_single_not_in_cache',
            args=(self.promo1.pk,)
        )

    @patch('panacea.engine.CacheEngine.store_cache')
    def testAllPass(self, patched_store):
        """
        по дефолту данный запрос проходит все проверки
        """

        r = self.client.get(self.url1)
        self.assertTrue(patched_store.called)
        self.assertEqual(r.status_code, 200)

    @patch('panacea.engine.CacheEngine.store_cache')
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

    @patch('panacea.engine.CacheEngine.store_cache')
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

    @patch('panacea.engine.CacheEngine.store_cache')
    def testContentType(self, patched_store):
        """
        проверим, что сохраняются только данные заданного формата
        в тестовом приложении мы сохраняем только application/json
        """
        url = self.url1 + '?format=xml'
        r = self.client.get(url)
        self.assertFalse(patched_store.called)
        self.assertEqual(r.status_code, 200)

    @patch('panacea.engine.CacheEngine.store_cache')
    def testScheme(self, patched_store):
        """
        данный url отсутствует в схеме кеширования
        """
        r = self.client.get(self.url1_no_cache)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

    @patch('panacea.engine.CacheEngine.store_cache')
    def testLocalDisabled(self, patched_store):
        from django.conf import settings
        settings.PCFG_CACHING['schemes']['api_promo_single']['enabled'] = False

        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

        settings.PCFG_CACHING['schemes']['api_promo_single']['enabled'] = True

    @patch('panacea.engine.CacheEngine.store_cache')
    def testGlobalDisabled(self, patched_store):
        from django.conf import settings
        settings.PCFG_ENABLED = False

        r = self.client.get(self.url1)
        self.assertEqual(r.status_code, 200)
        self.assertFalse(patched_store.called)

        settings.PCFG_ENABLED = True