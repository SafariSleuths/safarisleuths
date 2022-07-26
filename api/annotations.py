import json
from typing import TypedDict, Optional, List

from api.redis_client import redis_client

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


def truncate_annotations_for_session(session_id: str) -> None:
    redis_client.delete(f'{REDIS_KEY}:sessions:{session_id}')


def save_annotations_for_session(session_id: str, annotations: List[Annotation]) -> None:
    __save_annotations(f'{REDIS_KEY}:sessions:{session_id}', annotations)


def fetch_annotations_for_session(session_id: str) -> List[Annotation]:
    return __fetch_annotations(f'{REDIS_KEY}:sessions:{session_id}')


def __save_annotations(key: str, annotations: List[Annotation]) -> None:
    for annotation in annotations:
        redis_client.hset(key, annotation['id'], json.dumps(annotation))


def __fetch_annotations(key: str) -> List[Annotation]:
    annotations = []
    for annotation_json in redis_client.hvals(key):
        annotations.append(json.loads(annotation_json))
    return annotations
