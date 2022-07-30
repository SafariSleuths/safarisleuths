import json
import time
from multiprocessing import Process
from typing import TypedDict, List, Optional

from flask import Blueprint, current_app

from api.annotations import read_annotations_for_collection
from api.collections import must_get_collection_id
from api.redis_client import redis_client
from api.retrain_embeddings import retrain_embeddings
from api.status_response import StatusResponse

JOBS_REDIS_KEY = 'retrain:jobs'
LOGS_REDIS_KEY = 'retrain:logs'

flask_blueprint = Blueprint('retrain_job', __name__)


class RetrainStatus(TypedDict):
    collection_id: str
    created_at: float
    status: str


class RetrainEventLog(TypedDict):
    collection_id: str
    created_at: float
    message: str


class GetRetrainStatusResponse(TypedDict):
    status: str
    job: Optional[RetrainStatus]


@flask_blueprint.post('/api/v1/retrain/embeddings')
def post_retrain_embeddings() -> StatusResponse:
    collection_id = must_get_collection_id()
    job = RetrainStatus(
        collection_id=collection_id,
        created_at=time.time(),
        status='created'
    )
    save_job_status_to_redis(job)

    new_annotations = read_annotations_for_collection(collection_id)
    new_annotations = [a for a in new_annotations if a['accepted']]
    if len(new_annotations) == 0:
        job['status'] = 'completed'
        save_job_status_to_redis(job)
        current_app.logger.info('Retraining skipped since there are no new annotations for training.')
        return {'status': 'ok'}

    Process(target=retrain_embeddings, args=(new_annotations,)).start()
    return {'status': 'ok'}


@flask_blueprint.get('/api/v1/retrain/status')
def get_retrain_status() -> GetRetrainStatusResponse:
    collection_id = must_get_collection_id()
    job = read_job_status_from_redis(collection_id) or RetrainStatus(
        collection_id=collection_id,
        created_at=0,
        status='not started'
    )
    return {'status': 'ok', 'job': job}


@flask_blueprint.delete('/api/v1/retrain/status')
def delete_retrain_job() -> StatusResponse:
    collection_id = must_get_collection_id()
    delete_job_status_from_redis(collection_id)
    truncate_job_logs(collection_id)
    return {'status': 'ok'}


@flask_blueprint.post('/api/v1/retrain/abort')
def abort_retrain_job() -> StatusResponse:
    collection_id = must_get_collection_id()
    job_status = read_job_status_from_redis(collection_id)
    job_status['status'] = 'aborted'
    save_job_status_to_redis(job_status)
    return {'status': 'ok'}


class GetRetrainLogsResponse(TypedDict):
    status: str
    logs: List[RetrainEventLog]


@flask_blueprint.get('/api/v1/retrain/logs')
def get_retrain_logs() -> GetRetrainLogsResponse:
    collection_id = must_get_collection_id()
    return {'status': 'ok', 'logs': read_event_logs(collection_id)}


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


def read_job_status_from_redis(collection_id: str) -> Optional[RetrainStatus]:
    status_json = redis_client.hget(JOBS_REDIS_KEY, collection_id)
    if status_json is None:
        return None
    return json.loads(status_json)


def save_job_status_to_redis(job_status: RetrainStatus) -> None:
    redis_client.hset(JOBS_REDIS_KEY, job_status['collection_id'], json.dumps(job_status, default=str))


def delete_job_status_from_redis(collection_id: str) -> None:
    redis_client.hdel(JOBS_REDIS_KEY, collection_id)
