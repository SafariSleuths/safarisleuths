from typing import TypedDict, List

from flask import request, Blueprint

from api.data_models.prediction_inputs import save_images_for_collection, delete_images_for_collection, \
    list_image_paths_for_collection
from api.endpoints.helpers import must_get_collection_id, StatusResponse

flask_blueprint = Blueprint('images', __name__)


class PostImagesResponse(TypedDict):
    status: str
    uploaded: List[str]


class GetImagesResponse(TypedDict):
    status: str
    images: List[str]


@flask_blueprint.get('/api/v1/images')
def get_images() -> GetImagesResponse:
    collection_id = must_get_collection_id()
    return {'status': 'ok', 'images': [f'/{i}' for i in list_image_paths_for_collection(collection_id)]}


@flask_blueprint.post('/api/v1/images')
def post_images() -> PostImagesResponse:
    collection_id = must_get_collection_id()
    files = request.files
    uploaded = save_images_for_collection(collection_id, files)
    return {'status': 'ok', 'uploaded': [f'/{i}' for i in uploaded]}


@flask_blueprint.delete('/api/v1/images')
def delete_images() -> StatusResponse:
    collection_id = must_get_collection_id()
    images: List[str] = request.get_json()
    delete_images_for_collection(collection_id, images)
    return {'status': 'ok'}
