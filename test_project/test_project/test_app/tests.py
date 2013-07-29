# coding: utf-8

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils import simplejson

from test_project.test_app import models


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


class TestAllowCachingSimpleMethods(BaseTestCaseMixin, TestCase):
    """
    класс тестирования метода принимающего решение
    о необходимости кеширования ответа от апи
    """
    def testMethodChk(self):
        """
        проверяем часть отвечающую за проверку метода запроса
        """
        pass
