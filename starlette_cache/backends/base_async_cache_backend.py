from abc import abstractmethod
from abc import ABC
from typing import Any, Optional


class BaseAsyncCacheBackend(ABC):
    @abstractmethod
    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement get"
        )

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement set"
        )

    @abstractmethod
    async def add(self, key: str, value: Any, ttl: int) -> Any:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement add"
        )

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement delete"
        )
