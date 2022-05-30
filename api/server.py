import os.path
import secrets
from typing import TypedDict, List

import flask
from flask import request, send_from_directory

from api.model import process_image
from api_response import ApiResponse, Status, PhotoMetrics, Prediction

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/data/<path:name>')
def data_download(name):
    return send_from_directory('data', name)


@app.route('/api/v1/session', methods=['GET'])
def session():
    return ApiResponse(Status.OK, session=secrets.token_hex(16)).to_dict()


@app.route('/api/v1/list_files', methods=['POST'])
def list_images():
    session_id = 0
    images = [f'data/inputs/{session_id}/{name}' for name in os.listdir(f'data/inputs/{session_id}')]
    images.sort()
    return {'status': 'ok', 'images': images}


@app.route('/api/v1/upload_files', methods=['POST'])
def upload_files():
    session_id = 0
    uploaded_files = []
    for file_name in request.files:
        os.makedirs(f'data/inputs/{session_id}', exist_ok=True)
        upload_path = f'data/inputs/{session_id}/{os.path.basename(file_name)}'
        request.files[file_name].save(upload_path)
        uploaded_files.append(upload_path)
    return {'status': 'ok', 'images': uploaded_files}


@app.route('/api/v1/delete_files', methods=['POST'])
def delete_files():
    session_id = 0
    data = request.get_json()
    deleted = []
    for file_name in data['files']:
        file_path = f'data/inputs/{session_id}/{os.path.basename(file_name)}'
        os.remove(file_path)
        deleted.append(file_path)
    return {'status': 'ok', 'deleted': deleted}


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    session_id = 0
    metrics: List[PhotoMetrics] = []
    for file_name in os.listdir(f'data/inputs/{session_id}'):
        file_name = os.path.basename(file_name)
        input_file = f'data/inputs/{session_id}/{file_name}'
        output_file = f'data/outputs/{session_id}/{file_name}'
        boxes = process_image(input_file, output_file)
        metrics.append(PhotoMetrics(
            file=file_name,
            annotated_file=f'/{output_file}',
            predictions=[Prediction(animal='zebra', count=len(boxes), boxes=boxes)]
        ))

    metrics.sort(key=lambda a: a['file'])
    return ApiResponse(status=Status.OK, photo_metrics=metrics).to_dict()


if __name__ == "__main__":
    app.run()
