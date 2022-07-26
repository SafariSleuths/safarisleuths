export interface Annotation {
  id: number;
  file_name: string;
  annotated_file_name: string | undefined;
  cropped_file_name: string | undefined;
  bbox: Array<number>;
  species_confidence: number;
  predicted_species: string;
  predicted_name: string;
  accepted: boolean | undefined;
  ignored: boolean | undefined;
}

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

interface AnnotationsResponse {
  annotations: Array<Annotation>;
}

export function fetchAnnotations(
  sessionID: string
): Promise<AnnotationsResponse> {
  return fetch("/api/v1/annotations", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  }).then((resp) => resp.json());
}
