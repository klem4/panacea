# coding: utf-8

import  re
from django.core.management.base import BaseCommand, CommandError
from django.core import urlresolvers
from django.template.loader import render_to_string

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
        schemes = self.get_schemes()
        if not schemes:
            raise CommandError("Schemes list is empty")

        for scheme in schemes:
            self.render(scheme)

    def get_schemes(self):
        return CacheScheme.all()

    def render(self, scheme):
        location = self.get_location(scheme)
        key = self.get_key(scheme)
        print location
        print key
        print "\n\n"

    def get_key(self, scheme):
        request = self.make_request(scheme)
        return scheme.generate_store_key(request)

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



