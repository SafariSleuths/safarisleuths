import re
from typing import TypedDict, List

import flask
from flask import request, Blueprint

from api.data_models.collections import Collection, save_collection_to_redis, read_collections_from_redis

flask_blueprint = Blueprint('collections', __name__)


class GetCollectionsResponse(TypedDict):
    status: str
    collections: List[Collection]


class PostCollectionRequest(TypedDict):
    status: str
    name: str


class PostCollectionResponse(TypedDict):
    status: str
    collection: Collection


@flask_blueprint.get('/api/v1/collections')
def get_collections() -> GetCollectionsResponse:
    return {'status': 'ok', 'collections': read_collections_from_redis()}


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
