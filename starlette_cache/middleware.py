import functools
from typing import Callable, Optional, Union

from starlette.datastructures import Headers, MutableHeaders
from starlette.requests import Request

from starlette.types import ASGIApp, Receive, Scope, Send, Message

from starlette_cache import utils
from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend
from starlette_cache.backends.base_cache_backend import BaseCacheBackend


class CacheMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        backend: Optional[Union[BaseCacheBackend, BaseAsyncCacheBackend]] = None,
        cache_ttl: int = 300,
        key_function: Optional[Callable] = None,
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
        self.app = app
        self.cache_backend = backend
        self.ttl = cache_ttl
        self.key_function = key_function or utils.get_cache_key
        self.request = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.cache_backend:
            self.request = Request(scope, receive, send)
            self.request.state.update_cache = False
            if self.request.method in {"GET", "HEAD"}:
                cache_key = self.key_function(self.request)
                message = await self.cache_backend.get(cache_key)
                if message:
                    await self.send(message, send, self.request.headers)
                    return
                else:
                    self.request.state.update_cache = True
        send = functools.partial(
            self.send, send=send, request_headers=self.request.headers
        )
        await self.app(scope, receive, send)

    async def send(
        self, message: Message, send: Send, request_headers: Headers
    ) -> None:
        if message["type"] != "http.response.start":
            await send(message)
            return

        message.setdefault("headers", [])
        headers = MutableHeaders(scope=message)

        if (
            "cookie" not in request_headers
            and headers.get("set-cookie")
            and "Cookie" in headers.get("vary")
        ):
            await send(message)
            return

        if "private" in headers.get("Cache-Control"):
            await send(message)

        headers["Cache-Control"] = str(self.ttl)

        try:
            should_update_cache = self.request.state.update_cache
        except AttributeError:
            await send(message)
            return

        if not should_update_cache:
            await send(message)
            return

        future = send(message)
        cache_key = self.key_function(self.request)

        if isinstance(self.cache_backend, BaseAsyncCacheBackend):
            await self.cache_backend.set(cache_key, message, self.ttl)
        else:
            self.cache_backend.set(cache_key, message, self.ttl)

        await future
