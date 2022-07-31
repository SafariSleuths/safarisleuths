from typing import List, TypedDict

from flask import Blueprint

from api.clients.s3_client import s3_bucket
from api.data_models.species import Species

flask_blueprint = Blueprint('known_individuals', __name__)


class KnownIndividual(TypedDict):
    name: str
    species: str
    example_image_src: str


class GetKnownIndividualsResponse(TypedDict):
    status: str
    individuals: List[KnownIndividual]


@flask_blueprint.get('/api/v1/known_individuals')
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
