# -*- coding: utf-8 -*-
import time
import logging
from threading import Lock

_logger = logging.getLogger(__name__)

try:
    import redis
except ImportError:
    redis = None


class RateLimiter:
    """Fixed-window counter. Uses Redis if REAL_ESTATE_REDIS_URL is
    configured (recommended for production / multi-worker deployments),
    otherwise falls back to a per-process in-memory dict (fine for local
    dev, NOT safe across multiple Odoo workers in production).
    """

    _memory_store = {}
    _memory_lock = Lock()
    _redis_client = None
    _redis_checked = False

    @classmethod
    def _get_redis(cls, env):
        if cls._redis_checked:
            return cls._redis_client
        cls._redis_checked = True
        if redis is None:
            return None
        url = env['ir.config_parameter'].sudo().get_param('real_estate.redis_url')
        if not url:
            return None
        try:
            cls._redis_client = redis.from_url(url, socket_timeout=1)
            cls._redis_client.ping()
        except Exception:
            _logger.warning('RateLimiter: could not connect to Redis, falling back to memory store.')
            cls._redis_client = None
        return cls._redis_client

    @classmethod
    def hit(cls, env, key: str, limit: int, window_seconds: int) -> bool:
        """Increments the counter for `key`. Returns True if the caller
        is still within `limit` for this window, False if the limit is
        exceeded (caller should raise RateLimitExceeded / OTPRateLimitExceeded).
        """
        client = cls._get_redis(env)
        if client is not None:
            return cls._hit_redis(client, key, limit, window_seconds)
        return cls._hit_memory(key, limit, window_seconds)

    @classmethod
    def _hit_redis(cls, client, key, limit, window_seconds):
        pipe = client.pipeline()
        pipe.incr(key, 1)
        pipe.expire(key, window_seconds, nx=True)
        count, _ = pipe.execute()
        return int(count) <= limit

    @classmethod
    def _hit_memory(cls, key, limit, window_seconds):
        now = time.time()
        with cls._memory_lock:
            bucket = cls._memory_store.get(key)
            if bucket is None or now - bucket['start'] > window_seconds:
                cls._memory_store[key] = {'start': now, 'count': 1}
                return True
            bucket['count'] += 1
            return bucket['count'] <= limit

    @classmethod
    def seconds_until_reset(cls, env, key: str, window_seconds: int) -> int:
        client = cls._get_redis(env)
        if client is not None:
            ttl = client.ttl(key)
            return max(ttl, 0)
        with cls._memory_lock:
            bucket = cls._memory_store.get(key)
            if not bucket:
                return 0
            elapsed = time.time() - bucket['start']
            return max(int(window_seconds - elapsed), 0)
