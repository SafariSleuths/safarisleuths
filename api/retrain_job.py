import json
from typing import TypedDict, List, Optional

from flask import Blueprint

from api import sessions
from api.redis_client import redis_client

JOBS_REDIS_KEY = 'retrain_jobs'
LOGS_REDIS_KEY = 'retrain_logs'

flask_blueprint = Blueprint('retrain_job', __name__)


class RetrainJob(TypedDict):
    session_id: str
    created_at: float
    status: str


class RetrainEventLog(TypedDict):
    session_id: str
    created_at: float
    message: str


class GetRetrainJobResponse(TypedDict):
    status: str
    job: Optional[RetrainJob]


@flask_blueprint.get('/api/v1/retrain_job')
def get_retrain_job() -> GetRetrainJobResponse:
    session_id = sessions.must_get_session_id()
    job = read_job(session_id) or RetrainJob(
        session_id=session_id,
        created_at=0,
        status='not started'
    )
    return {'status': 'ok', 'job': job}


class GetRetrainLogsResponse(TypedDict):
    status: str
    logs: List[RetrainEventLog]


@flask_blueprint.get('/api/v1/retrain_logs')
def get_retrain_logs() -> GetRetrainLogsResponse:
    session_id = sessions.must_get_session_id()
    return {'status': 'ok', 'logs': read_event_logs(session_id)}


def truncate_job_logs(session_id: str) -> None:
    redis_client.delete(f'{LOGS_REDIS_KEY}:{session_id}')


def log_event(event: RetrainEventLog) -> None:
    event_json = json.dumps(event)
    redis_client.lpush(f"{LOGS_REDIS_KEY}:{event['session_id']}", event_json)


def read_event_logs(session_id: str) -> List[RetrainEventLog]:
    events = []
    for event_json in redis_client.lrange(f'{LOGS_REDIS_KEY}:{session_id}', 0, -1):
        events.append(json.loads(event_json))
    return events


def read_job(job_id: str) -> Optional[RetrainJob]:
    job_json = redis_client.hget(JOBS_REDIS_KEY, job_id)
    if job_json is None:
        return None
    return json.loads(job_json)


def save_job(job: RetrainJob) -> None:
    redis_client.hset(JOBS_REDIS_KEY, job['session_id'], json.dumps(job, default=str))
