import { Annotation } from "../actions/Annotations";

interface PredictionResponse {
  annotations: Array<Annotation>;
}

export function fetchPredictions(
  sessionID: string
): Promise<PredictionResponse> {
  return fetch("/api/v1/predictions", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  }).then((resp) => resp.json());
}
