from __future__ import annotations

from typing import List, TypedDict

from flask import Blueprint

from api.data_models.species import Species

flask_blueprint = Blueprint('species', __name__)


class GetSpeciesResponse(TypedDict):
    status: str
    species: List[str]


@flask_blueprint.get('/api/v1/species')
def get_species() -> GetSpeciesResponse:
    return {'status': 'ok', 'species': [x.value for x in Species]}
