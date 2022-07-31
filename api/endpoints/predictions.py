from typing import TypedDict, List

from flask import Blueprint

from api.data_models.annotations import Annotation, truncate_annotations_for_collection, save_annotations_for_collection
from api.endpoints.helpers import must_get_collection_id
from api.predictions.predict_bounding_boxes import predict_bounding_boxes_for_collection
from api.predictions.predict_individual import predict_individuals_from_yolov_predictions

flask_blueprint = Blueprint('predictions', __name__)


class PostPredictionsResponse(TypedDict):
    status: str
    annotations: List[Annotation]


UNDETECTED = 'undetected'


@flask_blueprint.post('/api/v1/predictions')
def post_predictions() -> PostPredictionsResponse:
    collection_id = must_get_collection_id()
    truncate_annotations_for_collection(collection_id)

    yolov_predictions = predict_bounding_boxes_for_collection(collection_id)
    individual_predictions = predict_individuals_from_yolov_predictions(yolov_predictions)

    yolov_predictions.sort(key=lambda p: p.cropped_file_name or '')
    individual_predictions.sort(key=lambda p: p.cropped_file_name or '')
    annotations = []
    for yolov_prediction, individual_prediction in zip(
            yolov_predictions, individual_predictions
    ):
        annotations.append(Annotation(
            id=yolov_prediction.id,
            file_name=yolov_prediction.file_name,
            annotated_file_name=yolov_prediction.annotated_file_name,
            cropped_file_name=yolov_prediction.cropped_file_name,
            bbox=yolov_prediction.bbox or [0, 0, 0, 0],
            species_confidence=yolov_prediction.confidence or 0,
            predicted_species=yolov_prediction.predicted_species or UNDETECTED,
            predicted_name=individual_prediction.individual_name or UNDETECTED,
            accepted=False,
            ignored=False,
        ))
    save_annotations_for_collection(collection_id, annotations)
    return {'status': 'ok', 'annotations': annotations}
