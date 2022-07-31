import flask

from typing import TypedDict

from api.data_models.collections import collection_exists


class StatusResponse(TypedDict):
    status: str


def must_get_collection_id() -> str:
    collection_id = flask.request.args.get('collectionID')
    if collection_id is not None:
        if collection_exists(collection_id):
            return collection_id
    flask.abort(400, f'Collection ID `{collection_id}` not found.')
