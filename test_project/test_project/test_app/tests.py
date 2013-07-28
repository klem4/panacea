# coding: utf-8

import mock
from mock import patch

from django.test import TestCase
from django.core.urlresolvers import reverse

from test_project.test_app import models

class BaseTestCaseMixin(object):
    def setUp(self):
        pass

    def tearDown(self):
        pass


class ApiSmokeTestCases(BaseTestCaseMixin, TestCase):
    """
    смоковые тесты апишек тестового приложения
    """

    def test_promo_single_smoke(self):
        promo = models.Promo.objects.create(name='promo1')

        self.assertEqual(self.client.get(
            reverse('api_promo_single', args=(promo.pk,)),
        ).status_code, 200)

    def test_promo_list_smoke(self):
        models.Promo.objects.create(name='promo1')
        models.Promo.objects.create(name='promo2')

        self.assertEqual(self.client.get(
            reverse('api_promo_list'),
        ).status_code, 200)


class TestEngineMiddlewareSmokeCalls(BaseTestCaseMixin, TestCase):
    """
    проверяем наличие корректных вызовов методов
    движда в middleware
    """
    def test_promo_single_smoke(self):
        promo = models.Promo.objects.create(name='promo1')

        from panacea.engine import CacheEngine
        with patch.object(CacheEngine, 'allow_caching') as patched_allow, \
            patch.object(CacheEngine, 'store_cache') as patched_store:

            patched_allow.return_value = True

            self.client.get(
                reverse('api_promo_single', args=(promo.pk,)),
            )

        patched_allow.assert_called()
        patched_store.assert_called_once_with()