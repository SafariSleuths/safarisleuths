import json
import secrets
import zlib
from typing import List, TypedDict

import flask
from flask import request, send_from_directory

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')

WEBSITE_DATA = 'api/website-data'
DEMO_PATH = WEBSITE_DATA + '/demo'


@app.get('/data/<path:name>')
def data_download(name):
    return send_from_directory(WEBSITE_DATA, name)


class SessionResponse(TypedDict):
    status: str
    session_id: str


@app.get('/api/v1/session')
def session() -> SessionResponse:
    return {'status': 'ok', 'session_id': secrets.token_hex(16)}


class ListFilesResponse(TypedDict):
    status: str
    images: List[str]


@app.post('/api/v1/list_files')
def list_files() -> ListFilesResponse:
    with open(DEMO_PATH + '/annotations.json') as f:
        blob = json.load(f)
    images: List[str] = [k['image_src'] for k in blob['annotations']]
    return {'status': 'ok', 'images': images}


@app.post('/api/v1/predict')
def predict():
    with open(DEMO_PATH + '/annotations.json') as f:
        blob = json.load(f)
    for k in blob['annotations']:
        if 'confidence' in k:
            continue
        k['confidence'] = (zlib.crc32(bytes(k['image_src'], 'utf8')) % 20 + 80) / 100
    return blob


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
    app.run()
