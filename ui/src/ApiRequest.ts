export type Status = "ok" | "error";

export interface SpeciesCount {
  animal: number;
  count: number;
}

export interface PhotoMetrics {
  file: string;
  annotated_file: string;
  predictions: Array<SpeciesCount>;
}

export interface PredictRequest {
  session_id: string;
}

export interface ApiResponse {
  status: Status;
  photo_metrics: Array<PhotoMetrics> | undefined;
  error: string | undefined;
}

export function fetchPhotoMetrics(req: PredictRequest): Promise<ApiResponse> {
  return fetch("/api/v1/predict", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(req),
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}
