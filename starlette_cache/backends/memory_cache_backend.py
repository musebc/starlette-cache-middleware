import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Optional

from starlette_cache.backends.base_cache_backend import BaseCacheBackend

_caches = {}
_expire_info = {}
_locks = {}


class MemoryCacheBackend(BaseCacheBackend):
    DEFAULT_TTL = 300

    def __init__(self, name):
        self.__cache = _caches.setdefault(name, OrderedDict())
        self.__expirations = _expire_info.setdefault(name, {})
        self.__lock = _locks.setdefault(name, Lock())

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        with self.__lock:
            if self.__has_expired(key):
                self.delete(key)
                return default
            value = self.__cache[key]
            self.__cache.move_to_end(key, last=False)
        return value

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        value_tuple = (time.time() + ttl, value)
        self.__cache[key] = value_tuple

    def add(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> Any:
        value_tuple = (time.time() + ttl, value)
        self.__cache[key] = value_tuple
        return value

    def delete(self, key: str):
        try:
            del self.__cache[key]
        except KeyError:
            pass

    def __has_expired(self, key):
        exp = self.__expirations.get(key, -1)
        return exp is not None and exp <= time.time()
