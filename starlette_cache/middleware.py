from typing import Callable, Optional, Union, Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from starlette.types import ASGIApp

from starlette_cache import utils
from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend
from starlette_cache.backends.base_cache_backend import BaseCacheBackend
from starlette_cache.backends.memory_cache_backend import MemoryCacheBackend


class CacheMiddleware:
    def __init__(
        self,
        app: Union[ASGIApp, Callable],
        backend: Optional[BaseCacheBackend] = None,
        cache_ttl: int = 300,
        key_function: Optional[Callable[[Request], str]] = None,
    ) -> None:
        """
        Create an instance of the cache middleware.
        :param app: The ASGI Application using this middleware.
        :param backend: An instance of a subclass of the BaseCacheBackend
        abstract base class. If no class is passed, then we will just set
        Cache-Control headers and return.
        :param cache_ttl: The time to live for the response in seconds.
        :param key_function: An optional function to generate the cache_key
        from the starlette Request object.
        """
        self.app: Union[ASGIApp, Callable] = app
        self.cache_backend: BaseCacheBackend = backend or MemoryCacheBackend
        self.ttl: int = cache_ttl
        self.key_func: Callable[[Request], str] = key_function or utils.get_cache_key
        self.request: Optional[Request] = None

    async def __call__(
        self, request: Request, response: Response, *args, **kwargs
    ) -> Any:
        self.request = request
        self.request.state.update_cache = False
        response = response
        if self.cache_backend:
            if self.request.method in {"GET", "HEAD"}:
                cache_key = self.key_func(self.request)
                message = self.cache_backend.get(cache_key)
                if message:
                    return message
                else:
                    self.request.state.update_cache = True
        message = await self.app(request=request, response=response, *args, **kwargs)
        return await self.build_response(message, self.request.headers, response)

    async def build_response(
        self, message: Any, request_headers: Headers, response: Response
    ) -> Any:

        headers = MutableHeaders()
        if (
            "cookie" not in request_headers
            and headers.get("set-cookie")
            and "Cookie" in headers.get("vary")
        ):
            return message

        if "private" in headers.get("Cache-Control", []):
            return message

        headers["Cache-Control"] = str(self.ttl)

        response.headers.update(dict(headers.items()))

        try:
            should_update_cache = self.request.state.update_cache
        except AttributeError:
            return message

        if not should_update_cache:
            return message

        cache_key = self.key_func(self.request)

        if isinstance(self.cache_backend, BaseAsyncCacheBackend):
            await self.cache_backend.set(cache_key, message, self.ttl)
        else:
            self.cache_backend.set(cache_key, message, self.ttl)

        return message
