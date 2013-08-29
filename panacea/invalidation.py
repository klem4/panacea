# coding: utf-8
from panacea import config as conf
from panacea.tools import get_aliases_by_models
from connection import redis_conn

conn = redis_conn()

def invalidate_all():
    conn.delete(
        *conn.keys('%s*' % conf.get('PCFG_KEY_PREFIX'))
    )


def invalidate_alias(aliases):
    if not isinstance(aliases, (list, tuple)):
        aliases = [aliases,]

    key_patterns = map(
        lambda alias: "%s%s*" % (
            conf.get('PCFG_KEY_PREFIX'), alias
        ),
        aliases
    )

    for p in key_patterns:
        conn.delete(*conn.keys(p))


def invalidate_model(models):
    aliases = get_aliases_by_models(models)
    invalidate_alias(aliases)
