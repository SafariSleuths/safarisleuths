from enum import Enum
from typing import TypedDict, List, Optional, Dict, Any

from api.model import Box


class Status(Enum):
    OK = "ok"
    ERROR = "error"


class Prediction(TypedDict):
    animal: str
    count: int
    boxes: List[Box]


class PhotoMetrics(TypedDict):
    file: str
    annotated_file: str
    predictions: List[Prediction]


class ApiResponse:
    def __init__(
            self,
            status: Status,
            photo_metrics: Optional[List[PhotoMetrics]] = None,
            error: Optional[str] = None,
            session: Optional[str] = None
    ):
        self.status = status
        self.photo_metrics = photo_metrics
        self.error = error
        self.session = session

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'photo_metrics': self.photo_metrics,
            'error': self.error,
            'session': self.session
        }
