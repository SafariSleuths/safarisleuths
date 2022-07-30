import json
import logging
from typing import List, TypedDict

import flask
from flask import send_from_directory
from werkzeug.exceptions import HTTPException

from api import retrain_classifier, retrain_job, images, labels, collections, annotations, predictions, species
from api.collections import save_collection_to_redis, Collection
from api.s3_client import s3_bucket
from api.species import Species

logging.basicConfig(
    format='%(asctime)s.%(msecs)d %(pathname)s:%(lineno)d [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S',
    level=logging.INFO
)

app = flask.Flask(__name__, static_url_path='', static_folder='ui/build')
app.register_blueprint(labels.flask_blueprint)
app.register_blueprint(species.flask_blueprint)
app.register_blueprint(collections.flask_blueprint)
app.register_blueprint(images.flask_blueprint)
app.register_blueprint(predictions.flask_blueprint)
app.register_blueprint(annotations.flask_blueprint)
app.register_blueprint(retrain_job.flask_blueprint)
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


@app.get('/website-data/<path:name>')
def get_website_data(name):
    return send_from_directory('website-data', name)


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


@app.get("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    save_collection_to_redis(Collection(id='Demo', name='Demo'))
    app.run()
