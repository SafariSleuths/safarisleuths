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
        k['confidence'] = (zlib.crc32(bytes(k['image_src'],'utf8')) % 20 + 80) / 100
    return blob

if __name__ == "__main__":
    app.run()
