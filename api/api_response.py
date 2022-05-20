from typing import TypedDict, List, Optional, Literal

Status = Literal["ok", "error"]


class SpeciesCount(TypedDict):
    species: str
    count: int


class PhotoMetrics(TypedDict):
    file: str
    predictions: List[SpeciesCount]


class ApiResponse(TypedDict):
    status: Status
    photo_metrics: PhotoMetrics


class ApiErrorResponse(TypedDict):
    status: Status
    error: str
