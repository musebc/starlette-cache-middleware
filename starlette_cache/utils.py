import hashlib
from collections import OrderedDict
from typing import List
from urllib.parse import quote

from starlette.datastructures import URL
from starlette.requests import Request


def get_cache_key(request: Request) -> str:
    return hashlib.md5(
        f"{request.method}.{__get_repeatable_url(request.url)}".encode("utf-8")
    ).hexdigest()


def get_cache_key_including_headers(request: Request, header_keys: List[str]) -> str:
    url = __get_repeatable_url(request.url)
    unsafe_header_string = ""
    for key in header_keys:
        value = request.headers.get(key)
        if value is not None:
            unsafe_header_string = f"{unsafe_header_string},{key}:{value}"

    header_string = quote(unsafe_header_string)
    return hashlib.md5(
        f"{request.method}.{url}.{header_string}".encode("utf-8")
    ).hexdigest()


def __get_repeatable_url(url: URL):
    return quote(f"{url.scheme}://{url.hostname}/{url.path}?{url.query}")


def __sorted_query_params(query_parameter_string: str):
    params = OrderedDict()

    param_list = query_parameter_string.split("&")
    param_list.sort(key=lambda x: x.split("=")[0])
    for param_string in param_list:
        param_key_and_val = param_string.split("=")
        params[param_key_and_val[0]] = param_key_and_val[1]
    return "&".join([f"{key}={value}" for (key, value) in params.items()])
