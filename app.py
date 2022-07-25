import os
from typing import List, TypedDict
import re

import PIL.Image
import flask
from flask import request, send_from_directory
import api.sessions as sessions
import api.inputs as inputs
from retrain_classifier import retrain_classifier
from api.annotations import Annotation, save_annotations_for_session, fetch_annotations_for_session
from api.redis_client import redis_client
from predict_bounding_boxes import predict_bounding_boxes, crop_and_upload, annotate_and_upload, BoundingBox
from predict_individual import predict_individuals_from_yolov_predictions

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')


class StatusResponse(TypedDict):
    status: str


def must_get_session_id() -> str:
    session_id = request.headers.get('SessionID', '')
    if session_id == '':
        flask.abort(400, 'Header `SessionID` required.')
    if not sessions.session_exists(session_id):
        flask.abort(400, f'Session ID `{session_id}` not found.')
    return session_id


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
    session_id = must_get_session_id()
    return {'status': 'ok', 'images': [f'/{i}' for i in inputs.image_paths_for_session(session_id)]}


@app.post('/api/v1/images')
def post_images() -> StatusResponse:
    session_id = must_get_session_id()
    inputs.save_images_for_session(session_id, request.files)
    return {'status': 'ok'}


class GetPredictionsResponse(TypedDict):
    status: str
    annotations: List[Annotation]


UNDETECTED = 'undetected'


@app.get('/api/v1/predictions')
def get_predictions() -> GetPredictionsResponse:
    session_id = must_get_session_id()
    yolov_predictions = []
    for input_image in inputs.read_images_for_session(session_id):
        yolov_predictions += predict_bounding_boxes(input_image, session_id)

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
            bbox_confidence=yolov_prediction.bbox_confidence or 0,
            predicted_species=yolov_prediction.predicted_species or UNDETECTED,
            predicted_name=individual_prediction.individual_name or UNDETECTED,
            accepted=False,
            ignored=False,
        ))
    return {'status': 'ok', 'annotations': annotations}


@app.post('/api/v1/annotations')
def post_annotations() -> StatusResponse:
    session_id = must_get_session_id()
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


@app.get('/api/v1/retrain')
def get_retrain_classifier():
    session_id = must_get_session_id()
    annotations = fetch_annotations_for_session(session_id)
    retrain_classifier(annotations)


@app.get("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    app.run()
