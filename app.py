import json
import logging
import os
from typing import List, TypedDict
import re

import PIL.Image
import flask
from flask import request, send_from_directory
from werkzeug.exceptions import HTTPException

import api.sessions as sessions
import api.inputs as inputs
from api import retrain_classifier
from api.annotations import Annotation, save_annotations_for_session, fetch_annotations_for_session
from api.predict_bounding_boxes import crop_and_upload, annotate_and_upload, BoundingBox, \
    predict_bounding_boxes_for_session
from api.predict_individual import predict_individuals_from_yolov_predictions
from api.s3_client import s3_bucket
from api.species import Species
from api.status_response import StatusResponse

logger = logging.getLogger(__name__)

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(pathname)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

app.register_blueprint(retrain_classifier.flask_blueprint)


@app.errorhandler(HTTPException)
def handle_exception(e):
    response = e.get_response()
    response.data = json.dumps({
        'status': 'failed',
        'error_code': e.code,
        'error_name': e.name,
        'error_reason': e.description,
    })
    response.content_type = 'application/json'
    return response


class GetSessionsResponse(TypedDict):
    status: str
    sessions: List[sessions.Session]


class PutSessionsRequest(TypedDict):
    name: str


class PutSessionsResponse(TypedDict):
    status: str
    session: sessions.Session


@app.get('/website-data/<path:name>')
def get_data(name):
    return send_from_directory('website-data', name)


@app.get('/api/v1/sessions')
def get_sessions() -> GetSessionsResponse:
    return {'status': 'ok', 'sessions': sessions.get_sessions()}


@app.put('/api/v1/sessions')
def put_sessions() -> StatusResponse:
    request_data: PutSessionsRequest = request.get_json()
    if 'name' not in request_data:
        flask.abort(400, 'field `name` required')
    session_name: str = request_data['name']
    session_id = session_name.replace(' ', '-').replace('_', '-')
    session_id = re.sub(r'[^\w\d-]', '', session_id).lower()
    session = {'id': session_id, 'name': session_name}
    sessions.save_session(session)
    return {'status': 'ok'}


class GetImagesResponse(TypedDict):
    status: str
    images: List[str]


@app.get('/api/v1/images')
def get_images() -> GetImagesResponse:
    session_id = sessions.must_get_session_id()
    return {'status': 'ok', 'images': [f'/{i}' for i in inputs.image_paths_for_session(session_id)]}


@app.post('/api/v1/images')
def post_images() -> StatusResponse:
    session_id = sessions.must_get_session_id()
    inputs.save_images_for_session(session_id, request.files)
    return {'status': 'ok'}


class GetPredictionsResponse(TypedDict):
    status: str
    annotations: List[Annotation]


UNDETECTED = 'undetected'


@app.get('/api/v1/predictions')
def get_predictions() -> GetPredictionsResponse:
    session_id = sessions.must_get_session_id()

    yolov_predictions = predict_bounding_boxes_for_session(session_id)
    individual_predictions = predict_individuals_from_yolov_predictions(yolov_predictions)

    yolov_predictions.sort(key=lambda p: p.cropped_file_name)
    individual_predictions.sort(key=lambda p: p.cropped_file_name)
    annotations = []
    for yolov_prediction, individual_prediction in zip(
            yolov_predictions, individual_predictions
    ):
        annotations.append(Annotation(
            id=os.path.basename(yolov_prediction.cropped_file_name),
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
    save_annotations_for_session(session_id, annotations)
    return {'status': 'ok', 'annotations': annotations}


class GetAnnotationsResponse(TypedDict):
    status: str
    annotations: List[Annotation]


@app.get('/api/v1/annotations')
def get_annotations() -> GetAnnotationsResponse:
    session_id = sessions.must_get_session_id()
    return {'status': 'ok', 'annotations': fetch_annotations_for_session(session_id)}


@app.post('/api/v1/annotations')
def post_annotations() -> StatusResponse:
    session_id = sessions.must_get_session_id()
    annotations: List[Annotation] = request.get_json()
    save_annotations_for_session(session_id, annotations)
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


class KnownIndividual(TypedDict):
    name: str
    species: str
    example_image_src: str


class GetKnownIndividualsResponse(TypedDict):
    status: str
    individuals: List[KnownIndividual]


@app.get('/api/v1/known_individuals')
def get_known_individuals() -> GetKnownIndividualsResponse:
    individuals = []
    for species in Species:
        for label in species.read_labels():
            for obj in s3_bucket.objects.filter(Prefix=f'{species.training_data_location()}{label}/'):
                print('obj.key')
                if obj.key.endswith('.jpg'):
                    individuals.append(KnownIndividual(
                        name=label,
                        species=species.value,
                        example_image_src=obj.key
                    ))
                    # Include 1 example for each individual.
                    break
    return {'status': 'ok', 'individuals': individuals}


class GetLabelsResponse(TypedDict):
    status: str
    labels: List[str]


@app.get('/api/v1/labels')
def get_labels() -> GetLabelsResponse:
    species_arg = request.args.get('species')
    if species_arg is None:
        flask.abort(400, f'Species required.')
    species = Species.from_string(species_arg)
    if species is None:
        flask.abort(400, f'No labels for {species_arg}.')
    return {'status': 'ok', 'labels': species.read_labels()}


class GetSpeciesResponse(TypedDict):
    status: str
    species: List[str]


@app.get('/api/v1/species')
def get_species() -> GetSpeciesResponse:
    return {'status': 'ok', 'species': [x.value for x in Species]}


@app.get("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    app.run()
