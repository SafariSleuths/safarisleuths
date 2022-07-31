import json
from typing import TypedDict, List

from api.clients.redis_client import redis_client

LOGS_REDIS_KEY = 'retrain:logs'


class RetrainEventLog(TypedDict):
    collection_id: str
    created_at: float
    message: str


def truncate_job_logs(collection_id: str) -> None:
    redis_client.delete(f'{LOGS_REDIS_KEY}:{collection_id}')


def log_event(event: RetrainEventLog) -> None:
    event_json = json.dumps(event)
    redis_client.rpush(f"{LOGS_REDIS_KEY}:{event['collection_id']}", event_json)


def read_event_logs(collection_id: str) -> List[RetrainEventLog]:
    events = []
    for event_json in redis_client.lrange(f'{LOGS_REDIS_KEY}:{collection_id}', 0, -1):
        events.append(json.loads(event_json))
    return events
