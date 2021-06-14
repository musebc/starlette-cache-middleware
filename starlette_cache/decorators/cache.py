import asyncio
import inspect
from functools import wraps
from typing import Callable, Optional, Any

from starlette.requests import Request
from starlette.responses import Response

from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend
from starlette_cache.backends.base_cache_backend import BaseCacheBackend
from starlette_cache.middleware import CacheMiddleware


def cache_api(
    cache_ttl: int,
    key_function: Optional[Callable] = None,
):
    def _decorator(endpoint):
        endpoint_type = None
        response_exists = False
        sig = inspect.signature(endpoint)
        for parameter in sig.parameters.values():
            if parameter.name == "request" or parameter.name == "websocket":
                endpoint_type = parameter.name
            if parameter.name == "response":
                response_exists = True
            if response_exists and endpoint_type:
                break
        else:
            if response_exists:
                raise ValueError(
                    f'No "request" or "websocket" argument on function "{endpoint}"'
                )
            else:
                raise ValueError(f'No "response" argument on function {endpoint}')
        if endpoint_type == "websocket":
            raise NotImplementedError("Websockets aren't supported yet.")
        elif asyncio.iscoroutinefunction(endpoint):
            middleware = CacheMiddleware(endpoint, cache_ttl, key_function)

            @wraps(endpoint)
            async def _wrapped_api(
                request: Request,
                response: Response,
                cache_backend: BaseAsyncCacheBackend,
                *args: Any,
                **kwargs: Any,
            ) -> Response:
                return await middleware(
                    request, response, cache_backend, *args, **kwargs
                )

            return _wrapped_api

        else:
            middleware = CacheMiddleware(endpoint, cache_ttl, key_function)

            @wraps(endpoint)
            def _wrapped_sync_api(
                request: Request,
                response: Response,
                cache_backend: BaseCacheBackend,
                *args: Any,
                **kwargs: Any,
            ):
                return asyncio.run(
                    middleware(request, response, cache_backend, *args, **kwargs)
                )

            return _wrapped_sync_api

    return _decorator
