from enum import Enum
from typing import TypedDict, List, Optional, Dict, Any


class Status(Enum):
    OK = "ok"
    ERROR = "error"


class ResponseType(Enum):
    ERROR = "error"
    PHOTO_METRICS = "photo_metrics"


class SpeciesCount(TypedDict):
    animal: str
    count: int


class PhotoMetrics(TypedDict):
    file: str
    predictions: List[SpeciesCount]


class ApiResponse:
    def __init__(self, status: Status, photo_metrics: Optional[List[PhotoMetrics]] = None, error: Optional[str] = None):
        self.status = status
        self.photo_metrics = photo_metrics
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status.value,
            'photo_metrics': self.photo_metrics,
            'error': self.error
        }
