import logging
import time
from typing import Any, Dict, Optional

import torch
from pytorch_lightning.loggers.base import LightningLoggerBase
from pytorch_lightning.utilities.rank_zero import rank_zero_only

from api.data_models.retrain_event_log import log_event, RetrainEventLog
from api.data_models.retrain_metrics import log_metrics, RetrainMetrics

log = logging.getLogger(__name__)


class RetrainEmbeddingsLogger(LightningLoggerBase):
    def __init__(self, collection_id: str, version: str):
        super().__init__()
        self.collection_id = collection_id
        self.__version = version
        self.__step_counter = 0

    @property
    def name(self) -> str:
        return "retrain_embeddings"

    @property
    def version(self) -> str:
        return self.__version

    @rank_zero_only
    def log_hyperparams(self, params: Dict[str, Any]):
        if len(params) > 0:
            pass

    @rank_zero_only
    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None) -> None:
        def _handle_value(value):
            if isinstance(value, torch.Tensor):
                return value.item()
            return value

        if step is None:
            step = self.__step_counter
        self.__step_counter += 1

        metrics = {k: _handle_value(v) for k, v in metrics.items()}
        epoch = metrics.get("epoch")
        train_loss_epoch = metrics.get("train_loss_epoch")

        if epoch is None or train_loss_epoch is None:
            return

        log_metrics(RetrainMetrics(
            collection_id=self.collection_id,
            step=step,
            epoch=epoch,
            train_loss_epoch=train_loss_epoch
        ))

        log_event(RetrainEventLog(
            collection_id=self.collection_id,
            created_at=time.time(),
            message=f'Epoch: {epoch} loss: {train_loss_epoch}.'
        ))
