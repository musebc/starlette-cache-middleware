from functools import wraps
from typing import Callable, Optional

from starlette.types import Receive, Scope, Send

from starlette_cache.backends.base_cache_backend import BaseCacheBackend
from starlette_cache.middleware import CacheMiddleware


def cache_api(
    backend: BaseCacheBackend, cache_ttl: int, key_function: Optional[Callable] = None
):
    def _decorator(endpoint):
        cache_middleware_class = CacheMiddleware

        middleware = cache_middleware_class(endpoint, backend, cache_ttl, key_function)

        @wraps(endpoint)
        def _wrapped_api(scope: Scope, receive: Receive, send: Send) -> None:
            await middleware(scope, receive, send)

        return _wrapped_api

    return _decorator
