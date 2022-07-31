import time
from multiprocessing import Process
from typing import TypedDict, List, Optional

from flask import Blueprint, current_app

from api.data_models.retrain_event_log import RetrainEventLog, truncate_job_logs, read_event_logs
from api.data_models.retrain_status import RetrainStatus, delete_job_status_from_redis, read_job_status_from_redis, \
    save_job_status_to_redis
from api.retraining.retraining_orchestrator import RetrainingOrchestrator
from api.endpoints.helpers import StatusResponse, must_get_collection_id

flask_blueprint = Blueprint('retrain_job', __name__)


class GetRetrainStatusResponse(TypedDict):
    status: str
    job: Optional[RetrainStatus]


class GetRetrainLogsResponse(TypedDict):
    status: str
    logs: List[RetrainEventLog]


@flask_blueprint.post('/api/v1/retrain/classifier')
def post_retrain_classifier() -> StatusResponse:
    collection_id = must_get_collection_id()
    save_job_status_to_redis(RetrainStatus(
        collection_id=collection_id,
        created_at=time.time(),
        status='created'
    ))
    trainer = RetrainingOrchestrator(
        collection_id=collection_id,
        logger=current_app.logger,
        classifier_only=True
    )
    Process(target=trainer.start_retraining, args=()).start()
    return {'status': 'ok'}


@flask_blueprint.post('/api/v1/retrain/embeddings')
def post_retrain_embeddings() -> StatusResponse:
    collection_id = must_get_collection_id()
    save_job_status_to_redis(RetrainStatus(
        collection_id=collection_id,
        created_at=time.time(),
        status='created'
    ))
    trainer = RetrainingOrchestrator(
        collection_id=collection_id,
        logger=current_app.logger,
        classifier_only=False
    )
    Process(target=trainer.start_retraining, args=()).start()
    return {'status': 'ok'}


@flask_blueprint.get('/api/v1/retrain/status')
def get_retrain_status() -> GetRetrainStatusResponse:
    collection_id = must_get_collection_id()
    job = read_job_status_from_redis(collection_id)
    return {'status': 'ok', 'job': job}


@flask_blueprint.delete('/api/v1/retrain/status')
def delete_retrain_status() -> StatusResponse:
    collection_id = must_get_collection_id()
    delete_job_status_from_redis(collection_id)
    truncate_job_logs(collection_id)
    return {'status': 'ok'}


@flask_blueprint.post('/api/v1/retrain/abort')
def post_retrain_abort() -> StatusResponse:
    collection_id = must_get_collection_id()
    job_status = read_job_status_from_redis(collection_id)
    job_status['status'] = 'aborted'
    save_job_status_to_redis(job_status)
    return {'status': 'ok'}


@flask_blueprint.get('/api/v1/retrain/logs')
def get_retrain_logs() -> GetRetrainLogsResponse:
    collection_id = must_get_collection_id()
    return {'status': 'ok', 'logs': read_event_logs(collection_id)}
