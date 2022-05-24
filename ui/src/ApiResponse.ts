import { useEffect, useState } from "react";

export type Status = "ok" | "error";

export interface SpeciesCount {
  animal: number;
  count: number;
}

export interface PhotoMetrics {
  file: string;
  predictions: Array<SpeciesCount>;
}

export interface PhotoMetricsRequest {
  files: Array<string>;
}

export interface ApiResponse {
  status: Status;
  photo_metrics: Array<PhotoMetrics> | undefined;
  error: string | undefined;
}

export function usePhotoMetrics(
  req: PhotoMetricsRequest
): ApiResponse | undefined {
  const [apiResponse, setApiResponse] = useState<ApiResponse | undefined>(
    undefined
  );
  useEffect(() => {
    fetchPhotoMetrics(req).then((data) => setApiResponse(data));
  }, [req.files.join(",")]);
  return apiResponse;
}

export function fetchPhotoMetrics(
  req: PhotoMetricsRequest
): Promise<ApiResponse> {
  return fetch("/api/v1/predict_counts", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(req),
  })
    .then((resp) => resp.json())
    .then((data) => data as ApiResponse);
}