import inspect
from functools import wraps
from typing import Callable, Optional, Any

from starlette.requests import Request
from starlette.responses import Response

from starlette_cache.backends.base_cache_backend import BaseCacheBackend
from starlette_cache.middleware import CacheMiddleware


def cache_api(
    backend: BaseCacheBackend,
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
            # middleware = WebsocketCacheMiddleware(endpoint, backend, cache_ttl,
            #                                       key_function)
            # @wraps(endpoint)
            # async def _wrapped_websocket(*args: Any, **kwargs: Any) -> None:
            #     await middleware(*args, **kwargs)
            # return _wrapped_websocket
            pass
        else:
            middleware = CacheMiddleware(endpoint, backend, cache_ttl, key_function)

            @wraps(endpoint)
            async def _wrapped_api(
                request: Request, response: Response, *args: Any, **kwargs: Any
            ) -> Response:
                return await middleware(request, response, *args, **kwargs)

            return _wrapped_api

    return _decorator
