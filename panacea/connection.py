import redis
import panacea.config as conf

_redis = None

def redis_conn():
    global _redis
    if not (_redis and _redis.ping()):
        _redis = redis.Redis(**conf.get('PCFG_REDIS'))
    return _redis
