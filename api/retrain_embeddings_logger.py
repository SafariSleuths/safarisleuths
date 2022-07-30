import logging
from typing import Any, Dict, Optional

import torch
from pytorch_lightning.loggers.base import LightningLoggerBase
from pytorch_lightning.utilities.rank_zero import rank_zero_only

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

        metrics = {k: _handle_value(v) for k, v in metrics.items()}
        metrics["step"] = step
        self.__step_counter += 1
        self.metrics.append(metrics)

    @rank_zero_only
    def finalize(self, status: str) -> None:
        # Optional. Any code that needs to be run after training
        # finishes goes here
        pass
