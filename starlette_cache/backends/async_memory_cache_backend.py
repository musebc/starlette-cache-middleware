import pickle
import time
import collections
import threading
from typing import Any, Optional

from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend

_caches = {}
_expire_info = {}
_locks = {}


class AsyncMemoryCacheBackend(BaseAsyncCacheBackend[str, Any]):
    DEFAULT_TTL = 300
    pickle_protocol = pickle.HIGHEST_PROTOCOL

    def __init__(self, name: str):
        self.__cache = _caches.setdefault(name, collections.OrderedDict())
        self.__expirations = _expire_info.setdefault(name, {})
        self.__lock = _locks.setdefault(name, threading.Lock())

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        with self.__lock:
            if await self.__has_expired(key):
                await self.delete(key)
                return default
            pickled = self.__cache[key]
            self.__cache.move_to_end(key, last=False)
        return pickle.loads(pickled)

    async def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        with self.__lock:
            await self._set(key, value, ttl)

    @staticmethod
    async def __get_expiration(ttl: int) -> float:
        return time.time() + ttl

    async def _set(self, key: str, value: Any, ttl: int) -> None:
        pickled = pickle.dumps(value, self.pickle_protocol)
        expiration = await self.__get_expiration(ttl)
        self.__cache[key] = pickled
        self.__cache.move_to_end(key, last=False)
        self.__expirations[key] = expiration

    async def add(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        with self.__lock:
            if await self.__has_expired(key):
                await self._set(key, value, ttl)
                return True
            return False

    async def delete(self, key: str) -> None:
        try:
            del self.__cache[key]
        except KeyError:
            pass
        try:
            del self.__expirations[key]
        except KeyError:
            pass

    async def __has_expired(self, key):
        exp = self.__expirations.get(key, -1)
        return exp is not None and exp <= time.time()
