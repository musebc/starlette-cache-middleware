from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from starlette_cache.backends.async_memory_cache_backend import AsyncMemoryCacheBackend
from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend
from starlette_cache.backends.memory_cache_backend import MemoryCacheBackend
from starlette_cache.middleware.cache_middleware import CacheMiddleware


@pytest.fixture(params=[AsyncMock, MagicMock])
def app(request):
    app_mock = request.param()
    yield app_mock
    app_mock.reset_mock()


@pytest.fixture(params=[AsyncMemoryCacheBackend, MemoryCacheBackend])
async def cache_backend(request):
    backend = request.param("test")
    yield backend
    await backend.set("test", None, 500) if isinstance(
        backend, BaseAsyncCacheBackend
    ) else backend.set("test", None, 500)


@pytest.mark.asyncio
class TestCacheMiddleware:
    cache_ttl = 500

    @staticmethod
    def key_function(x):
        return "test"

    @pytest.fixture
    def request_mock(self):
        request_mock = MagicMock(spec=Request)
        request_mock.method = "GET"
        yield request_mock

    @pytest.fixture
    def response_mock(self):
        response_mock = MagicMock(spec=Response)
        response_mock.headers = {}
        yield response_mock

    async def test_sets_message_from_app(
        self, app, cache_backend, request_mock, response_mock
    ):
        app.return_value = "message"
        middleware = CacheMiddleware(app, self.cache_ttl, self.key_function)
        await middleware(request_mock, response_mock, cache_backend)
        app.assert_called_once_with(request=request_mock, response=response_mock)
        cache_value = (
            await cache_backend.get("test")
            if isinstance(cache_backend, BaseAsyncCacheBackend)
            else cache_backend.get("test")
        )
        assert cache_value == "message"
        assert response_mock.headers["cache-control"] == str(self.cache_ttl)

    async def test_returns_value_from_cache(
        self, app, cache_backend, request_mock, response_mock
    ):
        await cache_backend.set("test", "message", 300) if isinstance(
            cache_backend, BaseAsyncCacheBackend
        ) else cache_backend.set("test", "message", 300)
        middleware = CacheMiddleware(app, self.cache_ttl, self.key_function)
        message = await middleware(request_mock, response_mock, cache_backend)
        app.assert_not_called()
        assert "message" == message
