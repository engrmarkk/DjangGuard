from redis import Redis
from backend.api_services.environmentals import REDIS_HOST, REDIS_PORT, REDIS_DB


class RedisService:
    def __init__(self):
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    def get(self, key):
        return self.redis.get(key)

    def set(self, key, value, expire=None):
        return self.redis.set(key, value, ex=expire)

    def delete(self, key):
        return self.redis.delete(key)
