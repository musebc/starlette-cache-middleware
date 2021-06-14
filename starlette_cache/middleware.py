import asyncio
from typing import Callable, Optional, Union, Any

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import Response

from starlette.types import ASGIApp

from starlette_cache import utils
from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend
from starlette_cache.backends.base_cache_backend import BaseCacheBackend


class CacheMiddleware:
    def __init__(
        self,
        app: Union[ASGIApp, Callable],
        cache_ttl: int = 300,
        key_function: Optional[Callable[[Request], str]] = None,
    ) -> None:
        """
        Create an instance of the cache middleware.
        :param app: The ASGI Application using this middleware.
        abstract base class. If no class is passed, then we will just set
        Cache-Control headers and return.
        :param cache_ttl: The time to live for the response in seconds.
        :param key_function: An optional function to generate the cache_key
        from the starlette Request object.
        """
        self.app: Union[ASGIApp, Callable] = app
        self.ttl: int = cache_ttl
        self.key_func: Callable[[Request], str] = key_function or utils.get_cache_key
        self.request: Optional[Request] = None

    async def __call__(
        self,
        request: Request,
        response: Response,
        cache_backend: Union[BaseCacheBackend, BaseAsyncCacheBackend],
        *args,
        **kwargs
    ) -> Any:
        """
        The wrapper for the ASGI application that handles caching requests and responses.
        :param request: The Starlette request
        :param response: The Starlette response
        :param cache_backend: An instance of a subclass of the BaseAsyncCacheBackend
        :param args: Arguments that are passed to the application
        :param kwargs: Keyword arguments passed to the application.
        :return: The Starlette response.
        """
        self.request = request
        self.request.state.update_cache = False
        response = response
        if cache_backend:
            if self.request.method in {"GET", "HEAD"}:
                cache_key = self.key_func(self.request)
                if isinstance(self.cache_backend, BaseAsyncCacheBackend):
                    message = await cache_backend.get(cache_key)
                else:
                    message = cache_backend.get(cache_key)
                if message:
                    return message
                else:
                    self.request.state.update_cache = True
        if asyncio.iscoroutinefunction(self.app):
            message = await self.app(
                request=request, response=response, *args, **kwargs
            )
        else:
            message = self.app(request=request, response=response, *args, **kwargs)
        return await self.build_response(message, response, cache_backend)

    async def build_response(
        self,
        message: Any,
        response: Response,
        cache_backend: Union[BaseCacheBackend, BaseAsyncCacheBackend],
    ) -> Any:
        """
        Builds the response object to return to the caller.
        :param message: The response from the ASGI application
        :param response: the response object
        :param cache_backend: The cache backend used to store responses.
        :return: The message returned from the ASGI application.
        """
        headers = MutableHeaders()

        headers["Cache-Control"] = str(self.ttl)

        response.headers.update(dict(headers.items()))

        try:
            should_update_cache = self.request.state.update_cache
        except AttributeError:
            return message

        if not should_update_cache:
            return message

        cache_key = self.key_func(self.request)

        await cache_backend.set(cache_key, message, self.ttl)

        return message
