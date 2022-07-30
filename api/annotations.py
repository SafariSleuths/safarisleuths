import json
from typing import TypedDict, Optional, List

from flask import request, Blueprint

from api.collections import must_get_collection_id
from api.redis_client import redis_client
from api.status_response import StatusResponse

REDIS_KEY = 'annotations'

flask_blueprint = Blueprint('annotations', __name__)


class Annotation(TypedDict):
    id: str
    file_name: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    bbox: Optional[List[float]]
    species_confidence: float
    predicted_species: str
    predicted_name: str
    accepted: bool
    ignored: bool


class GetAnnotationsResponse(TypedDict):
    status: str
    annotations: List[Annotation]


@flask_blueprint.get('/api/v1/annotations')
def get_annotations() -> GetAnnotationsResponse:
    collection_id = must_get_collection_id()
    return {'status': 'ok', 'annotations': read_annotations_for_collection(collection_id)}


@flask_blueprint.post('/api/v1/annotations')
def post_annotations() -> StatusResponse:
    collection_id = must_get_collection_id()
    annotations: List[Annotation] = request.get_json()
    save_annotations_for_collection(collection_id, annotations)
    for annotation in annotations:
        image = PIL.Image.open(annotation['file_name'])
        bbox = BoundingBox(
            x=annotation['bbox'][0],
            y=annotation['bbox'][1],
            w=annotation['bbox'][2],
            h=annotation['bbox'][3]
        )
        crop_and_upload(image.copy(), annotation['cropped_file_name'], bbox)
        annotate_and_upload(image.copy(), annotation['annotated_file_name'], bbox)
    return {'status': 'ok'}


def truncate_annotations_for_collection(collection_id: str) -> None:
    key = __key_for_collection(collection_id)
    redis_client.delete(key)


def save_annotations_for_collection(collection_id: str, annotations: List[Annotation]) -> None:
    key = __key_for_collection(collection_id)
    for annotation in annotations:
        redis_client.hset(key, annotation['id'], json.dumps(annotation))


def read_annotations_for_collection(collection_id: str) -> List[Annotation]:
    key = __key_for_collection(collection_id)
    annotations = []
    for annotation_json in redis_client.hvals(key):
        annotations.append(json.loads(annotation_json))
    return annotations


def __key_for_collection(collection_id: str) -> str:
    return f'{REDIS_KEY}:collections:{collection_id}'
