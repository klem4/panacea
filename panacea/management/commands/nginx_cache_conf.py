# coding: utf-8

import  re

from django.core.management.base import BaseCommand, CommandError
from django.core import urlresolvers
from django.template.loader import render_to_string

from panacea.schemes import CacheScheme
from panacea.tools import get_logger
from panacea import config as conf

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
        schemes = self.get_schemes()
        if not schemes:
            raise CommandError("Schemes list is empty")

        items = map(
            lambda scheme: {
                'location': self.get_location(scheme),
                'redis_key': self.get_redis_key(scheme)
            }, schemes
        )

        rendered_config = render_to_string(
            'config.html', {
                'items': items,
                'redis':conf.get('PCFG_REDIS'),
                'default_type': conf.get('PCFG_ALLOWED_CONTENT_TYPE')
            }
        )

        print rendered_config

    def get_schemes(self, **kwargs):
        return CacheScheme.all()

    def get_redis_key(self, scheme):
        request = self.make_request(scheme)
        return scheme.generate_store_key(request)

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

    def make_request(self, scheme):

        _get = dict(map(
            lambda key: (key, '$arg_%s' % key),
            scheme.get_all_part_keys('GET')
        ))

        _cookies = dict(map(
            lambda key: (key, '$cookie_%s' % key),
            scheme.get_all_part_keys('COOKIES')
        ))

        _meta = dict(map(
            lambda key: (key, '$%s' % key),
            scheme.get_all_part_keys('META')
        ))

        _path = '$uri'

        return FakeRequest(
            path=_path,
            query_string_dict=_get,
            cookies_dict=_cookies,
            headers_dict=_meta
        )
