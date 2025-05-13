from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import redis
import redis.asyncio as aioredis

__all__ = ["REQUEST_TRACK_SETTINGS", "redis_url", "redis_key", "redis_client"]


class LazySettingsDict:
    def __init__(self, key: str, default: dict | None = None):
        self.key = key
        self._default = default or {}

    def _get_settings(self) -> dict:
        return getattr(settings, self.key, self._default)

    def get(self, key, default=None):
        return self._get_settings().get(key, default)

    def __getitem__(self, key):
        return self._get_settings()[key]

    def __contains__(self, key):
        return key in self._get_settings()

    def keys(self):
        return self._get_settings().keys()

    def items(self):
        return self._get_settings().items()

    def values(self):
        return self._get_settings().values()

    def __repr__(self):
        return repr(self._get_settings())

    def __len__(self):
        return len(self._get_settings())


REQUEST_TRACK_SETTINGS = LazySettingsDict("REQUEST_TRACK_SETTINGS")


# Initialize Redis client if settings are configured
if REQUEST_TRACK_SETTINGS.get("USE_REDIS_BUFFER", False):
    redis_url = REQUEST_TRACK_SETTINGS.get("REDIS_URL", None)
    redis_key = REQUEST_TRACK_SETTINGS.get("REDIS_KEY", None)
    if not redis_url:
        raise ImproperlyConfigured(
            "Redis buffer is enabled but 'REDIS_URL' in REQUEST_TRACK_SETTINGS is missing. "
            "Please add a valid Redis URL (e.g., 'redis://localhost:6379/0') or "
            "set 'USE_REDIS_BUFFER': False to disable Redis buffering."
        )
    if not redis_key:
        raise ImproperlyConfigured(
            "Redis buffer is enabled but 'REDIS_KEY' in REQUEST_TRACK_SETTINGS is missing. "
            "Please specify a Redis list key name for storing logs."
        )
    try:
        redis_client = redis.Redis.from_url(redis_url)
        aredis_client = aioredis.from_url(redis_url)

        redis_client.ping()
    except (ValueError, redis.exceptions.ConnectionError) as e:
        raise ImproperlyConfigured(
            f"Invalid Redis configuration: {str(e)}. "
            f"Please check your REDIS_URL ('{redis_url}') and ensure Redis server is running."
        )
else:
    redis_client = None
    aredis_client = None
    redis_url = None
    redis_key = None
