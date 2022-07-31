from typing import TypedDict, List

import flask
from flask import Blueprint, request

from api.data_models.species import Species

flask_blueprint = Blueprint('labels', __name__)


class GetLabelsResponse(TypedDict):
    status: str
    labels: List[str]


@flask_blueprint.get('/api/v1/labels')
def get_labels() -> GetLabelsResponse:
    species_arg = request.args.get('species')
    if species_arg is None:
        flask.abort(400, f'Species required.')
    species = Species.from_string(species_arg)
    if species is None:
        flask.abort(400, f'No labels for {species_arg}.')
    return {'status': 'ok', 'labels': species.read_labels()}
