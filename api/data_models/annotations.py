import json
from typing import TypedDict, Optional, List

from api.clients.redis_client import redis_client

REDIS_KEY = 'annotations'


class Annotation(TypedDict):
    id: str
    file_name: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    bbox: Optional[List[float]]
    species_confidence: float
    predicted_species: str
    predicted_name: str
    accepted: bool
    ignored: bool


def truncate_annotations_for_collection(collection_id: str) -> None:
    key = __key_for_collection(collection_id)
    redis_client.delete(key)


def save_annotations_for_collection(collection_id: str, annotations: List[Annotation]) -> None:
    key = __key_for_collection(collection_id)
    for annotation in annotations:
        redis_client.hset(key, annotation['id'], json.dumps(annotation))


def read_annotations_for_collection(collection_id: str) -> List[Annotation]:
    key = __key_for_collection(collection_id)
    annotations = []
    for annotation_json in redis_client.hvals(key):
        annotations.append(json.loads(annotation_json))
    return annotations


def __key_for_collection(collection_id: str) -> str:
    return f'{REDIS_KEY}:collections:{collection_id}'
