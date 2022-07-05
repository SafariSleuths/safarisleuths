import json
import os.path
import secrets
import zlib
from typing import List, TypedDict, Any, Dict

import flask
from flask import request, send_from_directory

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/data/<path:name>')
def data_download(name):
    return send_from_directory('website-data', name)


class SessionResponse(TypedDict):
    status: str
    session_id: str


@app.route('/api/v1/session', methods=['GET'])
def session() -> SessionResponse:
    return {'status': 'ok', 'session_id': secrets.token_hex(16)}


class ListFilesResponse(TypedDict):
    status: str
    images: List[str]


@app.route('/api/v1/list_files', methods=['POST'])
def list_files() -> ListFilesResponse:
    with open('website-data/demo/annotations.json') as f:
        blob = json.load(f)
    images: List[str] = [k['image_src'] for k in blob['annotations']]
    return {'status': 'ok', 'images': images}


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    with open('website-data/demo/annotations.json') as f:
        blob = json.load(f)
    for k in blob['annotations']:
        if 'confidence' in k:
            continue
        k['confidence'] = (zlib.crc32(bytes(k['image_src'], 'utf8')) % 20 + 80) / 100
    return blob


@app.route('/api/v1/annotations', methods=['GET', 'POST'])
def annotations():
    if request.method == 'GET':
        return get_annotations()
    else:
        return post_annotations()


def get_annotations():
    with open('website-data/demo/annotations.json') as f:
        blob = json.load(f)
    return blob


def post_annotations():
    with open('website-data/demo/annotations.json') as f:
        blob = json.load(f)

    annotation_by_id = {annotation['id']: annotation for annotation in blob['annotations']}
    updates = request.get_json()
    for annotation in updates:
        annotation_by_id[annotation['id']] = annotation
    blob = {'annotations': [annotation for annotation in annotation_by_id.values()]}
    with open('website-data/demo/annotations.json', 'w') as f:
        json.dump(blob, f)
    return blob


if __name__ == "__main__":
    app.run()
