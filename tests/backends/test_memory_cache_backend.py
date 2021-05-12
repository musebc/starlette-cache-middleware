from unittest.mock import patch, MagicMock

import pytest

from starlette_cache.backends.memory_cache_backend import MemoryCacheBackend


class ExampleClass(object):
    def __init__(self, value: str):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, ExampleClass) and self.value == other.value


test_values = [
    1,
    "a",
    ["a", "b", 1],
    (),
    (1, "a"),
    {1, 2},
    {"a": "value", "b": 1, 3: ExampleClass("a")},
]


@pytest.fixture
def backend():
    mc_backend = MemoryCacheBackend("test_backend")
    yield mc_backend
    mc_backend.delete("test_key")


class TestMemoryCacheBackend:
    TEST_KEY = "test_key"

    @pytest.mark.parametrize("value", test_values)
    def test_get_from_cache(self, backend, value):
        backend.set(self.TEST_KEY, value, 10000)
        cache_value = backend.get(self.TEST_KEY)
        if type(value) is dict:
            for key, val in cache_value.items():
                assert value.get(key) == val
        else:
            assert value == cache_value

    @patch("collections.OrderedDict")
    def test_get_expired_deletes_and_returns_default(self, od_mock: MagicMock, backend):
        ordered_dict_mock = MagicMock()
        od_mock.return_value = ordered_dict_mock
        backend.set(self.TEST_KEY, "value", -1)
        assert len(backend._MemoryCacheBackend__cache) == 1
        assert backend.get(self.TEST_KEY) is None
        assert len(backend._MemoryCacheBackend__cache) == 0

    @patch("threading.Lock")
    def test_set_calls_lock(self, lock_mock, backend):
        test_mock = MagicMock()
        lock_mock.return_value = test_mock
        backend = MemoryCacheBackend("test")
        backend.set("key", "value")
        test_mock.__enter__.assert_called_once()
        test_mock.__exit__.assert_called_once()

    def test_add_returns_false_when_existing(self, backend):
        backend.set(self.TEST_KEY, 1)
        assert not backend.add(self.TEST_KEY, 3)

    def test_add_returns_true_when_missing(self, backend):
        assert backend.add(self.TEST_KEY, 4)

    def test_add_returns_true_when_expired(self, backend):
        backend.set(self.TEST_KEY, 1, -1)
        assert backend.add(self.TEST_KEY, 1)

    @pytest.mark.parametrize("value", test_values)
    def test_delete_from_cache(self, backend, value):
        backend.set(self.TEST_KEY, value, 10000)
        cache_value = backend.get(self.TEST_KEY)
        assert cache_value is not None
        backend.delete(self.TEST_KEY)
        assert backend.get(self.TEST_KEY) is None
