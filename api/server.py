import os.path
import secrets
from typing import List, TypedDict

import flask
from flask import request, send_from_directory

from api.model import process_image, BoundingBox

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')


@app.route('/data/<path:name>')
def data_download(name):
    return send_from_directory('data', name)


@app.route('/api/v1/session', methods=['GET'])
def session():
    return {'status': 'ok', 'session': secrets.token_hex(16)}


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


class AnimalPrediction(TypedDict):
    species: str
    animal_id: int
    boxes: List[BoundingBox]


class ImagePredictions(TypedDict):
    file: str
    annotated_url: str
    predictions: List[AnimalPrediction]


class AnimalSummary(TypedDict):
    animal_id: int
    species: str
    appearances: int


class PredictionResponse(TypedDict):
    status: str
    results: List[ImagePredictions]
    summary: List[AnimalSummary]


@app.route('/api/v1/predict', methods=['POST'])
def predict():
    session_id = 0

    image_predictions: List[ImagePredictions] = []
    for file_name in os.listdir(f'data/inputs/{session_id}'):
        file_name = os.path.basename(file_name)
        input_file = f'data/inputs/{session_id}/{file_name}'
        output_file = f'data/outputs/{session_id}/{file_name}'
        boxes = process_image(input_file, output_file)

        # The untrained model (resnet) makes one box prediction per zebra.
        # Once we fine-tune, we can expect to have multiple boxes per zebra that indicate
        # the different features: tail, feet, head, etc.
        boxes_by_animal_id = {}
        for box in boxes:
            animal_id = box['animal_id']
            if animal_id not in boxes_by_animal_id:
                boxes_by_animal_id[animal_id] = []
            boxes_by_animal_id[animal_id].append(box)

        image_predictions.append(ImagePredictions(
            file=file_name,
            annotated_url=f'/{output_file}',
            predictions=[
                AnimalPrediction(
                    species='zebra',
                    animal_id=animal_id,
                    boxes=boxes_by_animal_id[animal_id]
                ) for animal_id in boxes_by_animal_id
            ]
        ))
    image_predictions.sort(key=lambda a: a['file'])

    appearances_by_animal_id = {}
    for image_prediction in image_predictions:
        for prediction in image_prediction['predictions']:
            animal_id = prediction['animal_id']
            if animal_id not in appearances_by_animal_id:
                appearances_by_animal_id[animal_id] = 0
            appearances_by_animal_id[animal_id] += 1
    summary = [
        AnimalSummary(
            animal_id=animal_id,
            species='zebra',
            appearances=appearances_by_animal_id[animal_id]
        ) for animal_id in appearances_by_animal_id
    ]
    summary.sort(key=lambda a: a['animal_id'])

    return PredictionResponse(status='ok', results=image_predictions, summary=summary)


if __name__ == "__main__":
    app.run()
