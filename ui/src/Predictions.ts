const Undetected = "undetected";

export interface Annotation {
  id: number;
  file_name: string;
  annotated_file_name: string | undefined;
  cropped_file_name: string | undefined;
  bbox: Array<number>;
  species_confidence: number;
  predicted_species: string;
  predicted_name: string;
  reviewed: boolean | undefined;
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
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}

const AnnotationsCacheKey = "prediction";

export function readAnnotationsCache(): Array<Annotation> | undefined {
  const localAnnotations = localStorage.getItem(AnnotationsCacheKey);
  if (localAnnotations !== null) {
    return JSON.parse(localAnnotations);
  }
  return undefined;
}

export function writeAnnotationsCache(annotations: Array<Annotation>) {
  localStorage.setItem(AnnotationsCacheKey, JSON.stringify(annotations));
}
