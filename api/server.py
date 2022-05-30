import os.path
import secrets
from typing import TypedDict, List

import flask
from flask import request, send_from_directory

from api.model import process_image
from api_response import ApiResponse, Status, PhotoMetrics, SpeciesCount

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/data/<path:name>')
def data_download(name):
    return send_from_directory('data', name)


@app.route('/api/v1/session', methods=['GET'])
def session():
    return ApiResponse(Status.OK, session=secrets.token_hex(16)).to_dict()


@app.route('/api/v1/upload_image', methods=['POST'])
def upload_image():
    session_id = request.form['session_id']
    for file_name in request.files:
        file_name = os.path.basename(file_name)
        upload_path = f'../ui/public/data/inputs/{session_id}/{file_name}'
        request.files[file_name].save(upload_path)


class PredictRequest(TypedDict):
    files: List[str]
    session_id: str


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    data: PredictRequest = request.get_json()
    metrics: List[PhotoMetrics] = []
    session_id = 0
    if 'session_id' in data:
        session_id = data['session_id']

    for file_name in data['files']:
        file_name = os.path.basename(file_name)
        input_file = f'data/inputs/{session_id}/{file_name}'
        output_file = f'data/outputs/{session_id}/{file_name}'
        count = process_image(input_file, output_file)
        metrics.append(PhotoMetrics(
            file=file_name,
            annotated_file=f'/{output_file}',
            predictions=[SpeciesCount(animal='zebra', count=count)]
        ))
    return ApiResponse(status=Status.OK, photo_metrics=metrics).to_dict()


if __name__ == "__main__":
    app.run()
