# coding: utf-8

import  re
from django.core.management.base import BaseCommand, CommandError
from django.core import urlresolvers
from django.template.loader import render_to_string

from panacea import config as conf
from panacea.schemes import CacheScheme
from panacea.tools import get_logger

logger = get_logger()

class FakeRequest(object):
    def __init__(self, path='', query_string_dict=None,
                 cookies_dict=None, headers_dict=None):
        self.GET = query_string_dict or {}
        self.COOKIES = cookies_dict or {}
        self.META = headers_dict or {}
        self.path = path


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
                raise CommandError('No scheme for alias %s' % alias)

            print self.get_location(scheme)

    def get_location(self, scheme):
        alias = scheme.alias

        urlconf = urlresolvers.get_resolver(None).reverse_dict.get(alias)
        if not urlconf:
            raise CommandError('No reverse match for api: %s' % alias)

        pattern = urlconf[1]
        replace_map = (
           (r'/\(\?P<.+?>(.+?)\)/', r'/\1/'),
            ('^/(.+)', '\1'),
            ('\$$', '')
        )

        for repl in replace_map:
            pattern = re.sub(repl[0], repl[1], pattern)

        return "~ ^/%s$" % pattern



