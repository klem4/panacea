# coding: utf-8
from panacea import config as conf
from panacea.tools import get_aliases_by_models
from connection import redis_conn

conn = redis_conn()


def delete(*keys):
    if keys:
        conn.delete(*keys)
    return keys


def invalidate_all():
    keys = conn.keys('%s*' % conf.get('PCFG_KEY_PREFIX'))
    return delete(*keys)


def invalidate_alias(aliases):
    if not isinstance(aliases, (list, tuple)):
        aliases = [aliases,]

    key_patterns = map(
        lambda alias: "%s%s*" % (
            conf.get('PCFG_KEY_PREFIX'), alias
        ),
        aliases
    )

    results = []
    for p in key_patterns:
        results += delete(*conn.keys(p))

    return results


def invalidate_model(models):
    aliases = get_aliases_by_models(models)
    return invalidate_alias(aliases)
