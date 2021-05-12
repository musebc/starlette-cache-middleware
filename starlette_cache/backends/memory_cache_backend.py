import pickle
import time
import collections
import threading
from typing import Any, Optional

from starlette_cache.backends.base_cache_backend import BaseCacheBackend

_caches = {}
_expire_info = {}
_locks = {}


class MemoryCacheBackend(BaseCacheBackend):
    DEFAULT_TTL = 300
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, name: str):
        self.__cache = _caches.setdefault(name, collections.OrderedDict())
        self.__expirations = _expire_info.setdefault(name, {})
        self.__lock = _locks.setdefault(name, threading.Lock())

    def get(self, key: str, default: Any = None) -> Optional[Any]:
        with self.__lock:
            if self.__has_expired(key):
                self.delete(key)
                return default
            pickled = self.__cache[key]
            self.__cache.move_to_end(key, last=False)
        return pickle.loads(pickled)

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        with self.__lock:
            self._set(key, value, ttl)

    @staticmethod
    def __get_expiration(ttl: int) -> float:
        return time.time() + ttl

    def _set(self, key: str, value: Any, ttl: int) -> None:
        pickled = pickle.dumps(value, self.pickle_protocol)
        expiration = self.__get_expiration(ttl)
        self.__cache[key] = pickled
        self.__cache.move_to_end(key, last=False)
        self.__expirations[key] = expiration

    def add(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        with self.__lock:
            if self.__has_expired(key):
                self._set(key, value, ttl)
                return True
            return False

    def delete(self, key: str) -> None:
        try:
            del self.__cache[key]
        except KeyError:
            pass
        try:
            del self.__expirations[key]
        except KeyError:
            pass

    def __has_expired(self, key):
        exp = self.__expirations.get(key, -1)
        return exp is not None and exp <= time.time()
