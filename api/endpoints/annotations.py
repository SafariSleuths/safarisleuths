from typing import TypedDict, List

from PIL import Image

from api.data_models.annotations import save_annotations_for_collection, Annotation, read_annotations_for_collection
from api.endpoints.helpers import StatusResponse, must_get_collection_id
from flask import request, Blueprint

from api.predictions.predict_bounding_boxes import BoundingBox, crop_and_upload, annotate_and_upload

flask_blueprint = Blueprint('annotations', __name__)


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
        image = Image.open(annotation['file_name'])
        bbox = BoundingBox(
            x=annotation['bbox'][0],
            y=annotation['bbox'][1],
            w=annotation['bbox'][2],
            h=annotation['bbox'][3]
        )
        crop_and_upload(image.copy(), annotation['cropped_file_name'], bbox)
        annotate_and_upload(image.copy(), annotation['annotated_file_name'], bbox)
    return {'status': 'ok'}
