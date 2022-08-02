import json
import logging
import os

import flask
from flask import send_from_directory
from werkzeug.exceptions import HTTPException

from api.clients.redis_client import redis_client
from api.data_models.retrain_event_log import LOGS_REDIS_KEY
from api.data_models.retrain_metrics import METRICS_REDIS_KEY
from api.data_models.retrain_status import JOBS_REDIS_KEY
from api.endpoints import images, labels, collections, annotations, species, predictions, retrain

APP_HOST = os.getenv('APP_HOST', 'localhost')
APP_PORT = int(os.getenv('APP_PORT', '5000'))

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
app.register_blueprint(retrain.flask_blueprint)


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


@app.get("/")
def serve():
    return send_from_directory(app.static_folder, 'index.html')


if __name__ == "__main__":
    redis_client.delete(JOBS_REDIS_KEY)
    redis_client.delete(LOGS_REDIS_KEY)
    redis_client.delete(METRICS_REDIS_KEY)
    app.run(port=APP_PORT, host=APP_HOST)
