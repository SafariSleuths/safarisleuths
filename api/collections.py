import json
import re
from typing import TypedDict, List

import flask
from flask import request, Blueprint

from api.redis_client import redis_client

REDIS_KEY = 'collections'

flask_blueprint = Blueprint('collections', __name__)


class Collection(TypedDict):
    id: str
    name: str


class GetCollectionsResponse(TypedDict):
    status: str
    collections: List[Collection]


@flask_blueprint.get('/api/v1/collections')
def get_collections() -> GetCollectionsResponse:
    return {'status': 'ok', 'collections': read_collections_from_redis()}


class PostCollectionRequest(TypedDict):
    name: str


class PostCollectionResponse(TypedDict):
    status: str
    collection: Collection


@flask_blueprint.post('/api/v1/collections')
def post_collection() -> PostCollectionResponse:
    request_data: PostCollectionRequest = request.get_json()
    if 'name' not in request_data:
        flask.abort(400, 'Field `name` required.')
    collection_name: str = request_data['name']
    collection_id = collection_name.replace(' ', '-').replace('_', '-')
    collection_id = re.sub(r'[^\w\d-]', '', collection_id).lower()
    if collection_name == "":
        flask.abort(400, 'Field `name` cannot be empty.')
    collection: Collection = {'id': collection_id, 'name': collection_name}
    save_collection_to_redis(collection)
    return {'status': 'ok', 'collection': collection}


def must_get_collection_id() -> str:
    collection_id = request.args.get('collectionID')
    if collection_id is not None:
        if collection_exists(collection_id):
            return collection_id
    flask.abort(400, f'Collection ID `{collection_id}` not found.')


def collection_exists(collection_id: str) -> bool:
    return redis_client.hget(REDIS_KEY, collection_id) is not None


def read_collections_from_redis() -> List[Collection]:
    return [json.loads(s) for s in redis_client.hvals(REDIS_KEY)]


def save_collection_to_redis(collection: Collection) -> None:
    redis_client.hset(REDIS_KEY, collection['id'], json.dumps(collection))
