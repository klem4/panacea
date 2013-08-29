# coding: utf-8
from panacea import config as conf
from panacea.tools import get_aliases_by_models
from connection import redis_conn


def invalidate_all():
    conn = redis_conn()
    conn.delete(
        *conn.keys('%s*' % conf.get('PCFG_KEY_PREFIX'))
    )


def invalidate_alias(aliases):
    if not isinstance(aliases, (list, tuple)):
        aliases = list(aliases)
    pass


def invalidate_model(models):
    aliases = get_aliases_by_models(models)
    invalidate_alias(aliases)
