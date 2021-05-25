from abc import abstractmethod
from abc import ABC
from typing import Optional, Generic, TypeVar

KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValueType")


class BaseCacheBackend(ABC, Generic[KeyType, ValueType]):  # pragma: no cover
    @abstractmethod
    def get(self, key: KeyType, default: ValueType = None) -> Optional[ValueType]:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement get"
        )

    @abstractmethod
    def set(self, key: KeyType, value: ValueType, ttl: int) -> None:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement set"
        )

    @abstractmethod
    def add(self, key: KeyType, value: ValueType, ttl: int) -> bool:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement add"
        )

    @abstractmethod
    def delete(self, key: KeyType) -> None:
        raise NotImplementedError(
            "Subclasses of BaseCacheBackend need to implement delete"
        )
