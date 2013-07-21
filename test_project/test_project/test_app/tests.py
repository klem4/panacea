# coding: utf-8

from django.test import TestCase
from django.core.urlresolvers import reverse

from test_project.test_app import models

class BaseTestCaseMixin(object):
    def setUp(self):
        pass

    def tearDown(self):
        pass


class ApiSmokeTestCases(TestCase):
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
