import json
from typing import TypedDict

from api.clients.redis_client import redis_client

JOBS_REDIS_KEY = 'retrain:jobs'


class RetrainStatus(TypedDict):
    collection_id: str
    created_at: float
    status: str


def read_job_status_from_redis(collection_id: str) -> RetrainStatus:
    status_json = redis_client.hget(JOBS_REDIS_KEY, collection_id)
    if status_json is None:
        return RetrainStatus(
            collection_id=collection_id,
            created_at=0,
            status='not started'
        )
    return json.loads(status_json)


def save_job_status_to_redis(job_status: RetrainStatus) -> None:
    redis_client.hset(JOBS_REDIS_KEY, job_status['collection_id'], json.dumps(job_status, default=str))


def delete_job_status_from_redis(collection_id: str) -> None:
    redis_client.hdel(JOBS_REDIS_KEY, collection_id)
