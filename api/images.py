import os
from typing import TypedDict, List

from flask import request, Blueprint
from werkzeug.datastructures import ImmutableMultiDict, FileStorage

from api.collections import must_get_collection_id
from api.s3_client import s3_bucket
from api.status_response import StatusResponse

flask_blueprint = Blueprint('images', __name__)

INPUTS_PATH = 'website-data/inputs'


class GetImagesResponse(TypedDict):
    status: str
    images: List[str]


@flask_blueprint.get('/api/v1/images')
def get_images() -> GetImagesResponse:
    collection_id = must_get_collection_id()
    return {'status': 'ok', 'images': [f'/{i}' for i in list_image_paths_for_collection(collection_id)]}


def list_image_paths_for_collection(collection_id: str) -> List[str]:
    return [o.key for o in s3_bucket.objects.filter(Prefix=f'{INPUTS_PATH}/{collection_id}/')]


class PostImagesResponse(TypedDict):
    status: str
    uploaded: List[str]


@flask_blueprint.post('/api/v1/images')
def post_images() -> PostImagesResponse:
    collection_id = must_get_collection_id()
    uploaded = save_images_for_collection(collection_id, request.files)
    return {'status': 'ok', 'uploaded': [f'/{i}' for i in uploaded]}


@flask_blueprint.delete('/api/v1/images')
def delete_images() -> StatusResponse:
    collection_id = must_get_collection_id()
    images: List[str] = request.get_json()
    delete_images_for_collection(collection_id, images)
    return {'status': 'ok'}


def save_images_for_collection(collection_id: str, files: ImmutableMultiDict[str, FileStorage]) -> List[str]:
    os.makedirs(f'{INPUTS_PATH}/{collection_id}', exist_ok=True)
    uploaded = []
    for file_name in files:
        dest = f'{INPUTS_PATH}/{collection_id}/{os.path.basename(file_name)}'
        files[file_name].save(dest)
        s3_bucket.upload_file(dest, dest)
        uploaded.append(dest)
    return uploaded


def delete_images_for_collection(collection_id: str, file_names: List[str]) -> None:
    real_file_names = []
    for file_name in file_names:
        real_file_names.append(f'{INPUTS_PATH}/{collection_id}/{os.path.basename(file_name)}')

    for file_name in real_file_names:
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass

    s3_bucket.delete_objects(Delete={'Objects': [{'Key': key} for key in real_file_names]})
