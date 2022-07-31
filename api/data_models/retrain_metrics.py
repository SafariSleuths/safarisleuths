import json
from typing import TypedDict, List

from api.clients.redis_client import redis_client

METRICS_REDIS_KEY = 'retrain:metrics'


class RetrainMetrics(TypedDict):
    collection_id: str
    step: int
    epoch: int
    train_loss_epoch: float


def truncate_metrics(collection_id: str) -> None:
    redis_client.delete(f'{METRICS_REDIS_KEY}:{collection_id}')


def log_metrics(metrics: RetrainMetrics) -> None:
    metrics_json = json.dumps(metrics)
    redis_client.rpush(f"{METRICS_REDIS_KEY}:{metrics['collection_id']}", metrics_json)


def read_metrics(collection_id: str) -> List[RetrainMetrics]:
    metrics = []
    for metrics_json in redis_client.lrange(f'{METRICS_REDIS_KEY}:{collection_id}', 0, -1):
        metrics.append(json.loads(metrics_json))
    return metrics
