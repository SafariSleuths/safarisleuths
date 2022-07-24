from __future__ import annotations
import json
from typing import List, TypedDict, Optional
import re
import flask
from flask import request, send_from_directory
import api.sessions as sessions
import api.inputs as inputs
from api.redis_client import redis_client
from predict_bounding_boxes import predict_bounding_boxes
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


class Annotation(TypedDict):
    id: int
    file_name: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    bbox: Optional[List[float]]
    bbox_confidence: float
    predicted_species: str
    predicted_name: str


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
    for annotation_id, yolov_prediction, individual_prediction in zip(
            range(len(yolov_predictions)), yolov_predictions, individual_predictions
    ):
        annotations.append(Annotation(
            id=annotation_id,
            file_name=yolov_prediction.file_name,
            annotated_file_name=yolov_prediction.annotated_file_name,
            cropped_file_name=yolov_prediction.cropped_file_name,
            bbox=yolov_prediction.bbox or [0, 0, 0, 0],
            bbox_confidence=yolov_prediction.bbox_confidence or 0,
            predicted_species=yolov_prediction.predicted_species or UNDETECTED,
            predicted_name=individual_prediction.individual_name or UNDETECTED,
        ))
    return {'status': 'ok', 'annotations': annotations}


@app.put('/api/v1/annotations')
def put_annotation():
    with open(DEMO_PATH + '/annotations.json') as f:
        blob = json.load(f)

    annotation_by_id = {annotation['id']: annotation for annotation in blob['annotations']}
    updates = request.get_json()
    for annotation in updates:
        annotation_by_id[annotation['id']] = annotation
    blob = {'annotations': [annotation for annotation in annotation_by_id.values()]}
    with open(DEMO_PATH + '/annotations.json', 'w') as f:
        json.dump(blob, f)
    return blob


@app.get("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    redis_client.hset(sessions.REDIS_KEY, 'Demo', '{"id":"Demo","name":"Demo"}')
    app.run()
