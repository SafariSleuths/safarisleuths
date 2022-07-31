import json
from typing import TypedDict, List

from api.clients.redis_client import redis_client

REDIS_KEY = 'collections'


class Collection(TypedDict):
    id: str
    name: str


def collection_exists(collection_id: str) -> bool:
    return redis_client.hget(REDIS_KEY, collection_id) is not None


def read_collections_from_redis() -> List[Collection]:
    return [json.loads(s) for s in redis_client.hvals(REDIS_KEY)]


def save_collection_to_redis(collection: Collection) -> None:
    redis_client.hset(REDIS_KEY, collection['id'], json.dumps(collection))
