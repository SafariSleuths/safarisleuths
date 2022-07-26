import json
from typing import TypedDict, List

from api.redis_client import redis_client

JOBS_REDIS_KEY = 'retrain_jobs'
LOGS_REDIS_KEY = 'retrain_logs'


class RetrainJob(TypedDict):
    session_id: str
    created_at: float
    status: str


class RetrainEventLog(TypedDict):
    session_id: str
    created_at: float
    message: str


def truncate_job_logs(session_id: str) -> None:
    redis_client.delete(f'{LOGS_REDIS_KEY}:{session_id}')


def log_event(event: RetrainEventLog) -> None:
    event_json = json.dumps(event)
    redis_client.lpush(f"{LOGS_REDIS_KEY}:{event['session_id']}", event_json)


def read_events(session_id: str) -> List[RetrainEventLog]:
    events = []
    for event_json in redis_client.lrange(f'{LOGS_REDIS_KEY}:{session_id}', 0, -1):
        events.append(json.loads(event_json))
    return events


def read_job(job_id: str) -> RetrainJob:
    return json.loads(redis_client.hget(JOBS_REDIS_KEY, job_id))


def save_job(job: RetrainJob) -> None:
    redis_client.hset(JOBS_REDIS_KEY, job['session_id'], json.dumps(job, default=str))
