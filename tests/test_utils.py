import hashlib
from urllib.parse import quote

import pytest
from starlette.requests import Request

from starlette_cache.utils import get_cache_key, get_cache_key_including_headers


@pytest.fixture
def starlette_request() -> Request:
    scope = dict(
        method="GET",
        type="http",
        path="test/v1/test",
        headers=[(b"test_header", b"test_val"), (b"test_header_1", b"test_val_2")],
        query_string=b"?b=1&a=2",
    )
    request = Request(scope)
    yield request


def test_default_cache_key_function(starlette_request: Request):
    key = get_cache_key(starlette_request)
    expected = hashlib.md5(
        f"GET.{quote('://None/test/v1/test?a=2&b=1')}".encode("utf-8")
    ).hexdigest()
    assert key == expected


def test_get_cache_key_with_headers(starlette_request):
    key = get_cache_key_including_headers(
        starlette_request, ["test_header", "test_header_1"]
    )
    expected = hashlib.md5(
        f"GET.{quote('://None/test/v1/test?a=2&b=1')}.{quote('test_header:test_val,test_header_1:test_val_2')}".encode(
            "utf-8"
        )
    ).hexdigest()
    assert key == expected
