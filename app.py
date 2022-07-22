from __future__ import annotations
import json
import os

import boto3
import redis
import zlib
from typing import List, TypedDict
import re

import flask
from flask import request, send_from_directory

from predict_bounding_boxes import predict_bounding_boxes, read_images, crop_image_to_bbox
from s3_client import s3_bucket

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')

WEBSITE_DATA = 'api/website-data'
DEMO_PATH = WEBSITE_DATA + '/demo'

redis_client = redis.Redis(decode_responses=True)

S3_BUCKET_URL = 'https://animal-id-sagemaker.s3-website-us-east-1.amazonaws.com'
LOCAL_INPUTS_PATH = 'website-data/inputs'
LOCAL_OUTPUTS_PATH = 'website-data/outputs'
S3_INPUTS_PATH = 'website-data/inputs'
S3_OUTPUTS_PATH = 'website-data/outputs'

REDIS_KEY_SESSIONS = 'sessions'


@app.get('/data/<path:name>')
def get_data(name):
    return send_from_directory(WEBSITE_DATA, name)


class Session(TypedDict):
    id: str
    name: str


class SessionsResponse(TypedDict):
    status: str
    sessions: List[Session]


def get_redis_sessions() -> List[Session]:
    return [json.loads(s) for s in redis_client.hvals(REDIS_KEY_SESSIONS)]


def session_exists(session_id: str) -> bool:
    return redis_client.hget(REDIS_KEY_SESSIONS, session_id) is not None


@app.get('/api/v1/sessions')
def get_sessions() -> SessionsResponse:
    sessions = [json.loads(s) for s in redis_client.hvals(REDIS_KEY_SESSIONS)]
    return {'status': 'ok', 'sessions': sessions}


class PutSessionRequest(TypedDict):
    name: str


class PutSessionResponse(TypedDict):
    status: str
    session: Session


@app.put('/api/v1/sessions')
def put_sessions() -> PutSessionResponse:
    request_data = request.get_json()
    if 'name' not in request_data:
        flask.abort(400, 'field `name` required')
    session_name: str = request_data['name']
    session_id = session_name.replace(' ', '-').replace('_', '-')
    session_id = re.sub(r'[^\w\d-]', '', session_id).lower()
    session = {'id': session_id, 'name': session_name}
    redis_client.hset(REDIS_KEY_SESSIONS, session['id'], json.dumps(session))
    return {'status': 'ok', 'session': session}


class ImagesResponse(TypedDict):
    status: str
    images: List[str]


def must_get_session_id() -> str:
    session_id = request.headers.get('SessionID', '')
    if session_id == '':
        flask.abort(400, 'Header `SessionID` required.')
    if not session_exists(session_id):
        flask.abort(400, f'Session ID `{session_id}` not found.')
    return session_id


@app.post('/api/v1/images')
def post_images() -> ImagesResponse:
    session_id = must_get_session_id()
    os.makedirs(f'{LOCAL_INPUTS_PATH}/{session_id}', exist_ok=True)
    uploaded = []
    for file_name in request.files:
        local_path = f'{LOCAL_INPUTS_PATH}/{session_id}/{os.path.basename(file_name)}'
        request.files[file_name].save(local_path)
        s3_path = f'{S3_INPUTS_PATH}/{session_id}/{os.path.basename(file_name)}'
        s3_bucket.upload_file(local_path, s3_path)
        uploaded.append(s3_path)
    return {'status': 'ok', 'images': uploaded}


@app.get('/api/v1/images')
def get_images() -> ImagesResponse:
    session_id = must_get_session_id()
    return {'status': 'ok', 'images': get_images_for_session(session_id)}


def get_images_for_session(session_id: str) -> List[str]:
    return [o.key for o in s3_bucket.objects.filter(Prefix=f'{S3_INPUTS_PATH}/{session_id}/')]


@app.route('/api/v1/predict')
def predict():
    session_id = must_get_session_id()
    file_names = get_images_for_session(session_id)
    input_images = read_images(file_names)

    predictions = []
    for input_image in input_images:
        predictions + predict_bounding_boxes(input_image, session_id)

@app.get('/api/v1/annotations')
def get_annotations():
    with open(DEMO_PATH + '/annotations.json') as f:
        blob = json.load(f)
    return blob


@app.post('/api/v1/annotations')
def post_annotations():
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
    redis_client.hset(REDIS_KEY_SESSIONS, 'Demo', '{"id":"Demo","name":"Demo"}')
    app.run()
