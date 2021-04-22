from abc import abstractmethod
from abc import ABC
from typing import Any, Optional


class BaseCacheBackend(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement get"
        )

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement set"
        )

    @abstractmethod
    def add(self, key: str, value: Any, ttl: int) -> Any:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement add"
        )

    @abstractmethod
    def delete(self, key: str):
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement delete"
        )
