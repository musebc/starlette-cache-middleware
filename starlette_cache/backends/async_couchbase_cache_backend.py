from typing import AnyStr, Union, Optional

from acouchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.cluster import ClusterOptions
from couchbase.collection import InsertOptions, UpsertOptions
from couchbase.exceptions import (
    CouchbaseException,
    DocumentExistsException,
    DocumentNotFoundException,
)

from starlette_cache.backends.base_async_cache_backend import BaseAsyncCacheBackend

CouchbaseKey = Union[AnyStr, int, float]
CouchbaseValue = Union[AnyStr, int, float]


class CouchbaseClient(object):
    @classmethod
    async def create_client(cls, *args, **kwargs):
        self = CouchbaseClient(*args)
        client = await self.ping()
        # need to check for more than just a result
        # shown as example starting point
        if not client:
            await self.connect(**kwargs)
        return self

    _instance = None

    def __new__(cls, host, bucket, username, pw):
        if CouchbaseClient._instance is None:
            CouchbaseClient._instance = object.__new__(cls)
            CouchbaseClient._instance.host = host
            CouchbaseClient._instance.bucket_name = bucket
            CouchbaseClient._instance.username = username
            CouchbaseClient._instance.password = pw
        return CouchbaseClient._instance

    async def connect(self, **kwargs):
        conn_str = "couchbase://{0}".format(self.host)

        try:
            cluster_opts = ClusterOptions(
                authenticator=PasswordAuthenticator(self.username, self.password),
                **kwargs
            )
            self._cluster = Cluster(conn_str, options=cluster_opts)
            self._bucket = self._cluster.bucket(self.bucket_name)
            await self._bucket.on_connect()
            self._collection = self._bucket.default_collection()
        except CouchbaseException as error:
            print("Could not connect to cluster. Error: {}".format(error))
            raise

    async def ping(self):
        try:
            return not self._bucket.closed
        except AttributeError:
            # if the _bucket attr doesn't exist, neither does the client
            return False

    async def get(self, key, **kwargs):
        return await self._collection.get(key, **kwargs)

    async def insert(self, key, doc, **kwargs):
        opts = InsertOptions(expiry=kwargs.get("expiry", None))
        return await self._collection.insert(key, doc, opts)

    async def upsert(self, key, doc, **kwargs):
        opts = UpsertOptions(expiry=kwargs.get("expiry", None))
        return await self._collection.upsert(key, doc, opts)

    async def remove(self, key):
        return await self._collection.remove(key)


class AsyncCouchbaseCacheBackend(BaseAsyncCacheBackend[CouchbaseKey, CouchbaseValue]):
    def __init__(self, client):
        self.__client = client

    @staticmethod
    async def get_instance(host: str, bucket: str, username: str, password: str):
        client = await CouchbaseClient.create_client(host, bucket, username, password)
        return AsyncCouchbaseCacheBackend(client)

    async def get(
        self, key: CouchbaseKey, default: CouchbaseValue = None
    ) -> Optional[CouchbaseValue]:
        try:
            result = await self.__client.get(key)
            return result.content
        except DocumentNotFoundException:
            return default

    async def set(self, key: CouchbaseKey, value: CouchbaseValue, ttl: int) -> None:
        await self.__client.upsert(key, value)

    async def add(self, key: CouchbaseKey, value: CouchbaseValue, ttl: int) -> bool:
        try:
            await self.__client.insert(key, value, timeout=ttl)
        except DocumentExistsException:
            return False
        return True

    async def delete(self, key: CouchbaseKey) -> None:
        await self.__client.remove(key)
