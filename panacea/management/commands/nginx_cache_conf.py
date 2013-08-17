# coding: utf-8

from django.core.management.base import BaseCommand
from panacea import config as conf
from panacea.schemes import CacheScheme
from panacea.tools import get_logger

logger = get_logger()

class Command(BaseCommand):
    help = u"построение блока кофигурации nginx " \
           u"для кеширования описанных в конфиге api"

    def handle(self, *args, **options):
        cache_schemes = self.get_schemes()

    def get_schemes(self):
        for alias in conf.get(
                'PCFG_CACHING', default={}
        ).get(
                'schemes', {}
        ).keys():
            scheme = CacheScheme.filter(alias=alias)
            if not scheme:
                logger.error('No scheme for alias %s' % alias)
                continue

            
