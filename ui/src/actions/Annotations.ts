import { StatusResponse } from "./StatusResponse";

export const Undetected = "undetected";

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

export function compareAnnotations(a: Annotation, b: Annotation): number {
  if (a.predicted_species != b.predicted_species) {
    switch (true) {
      case a.predicted_species === Undetected:
        return 1;
      case b.predicted_species === Undetected:
        return -1;
      default:
        return a.predicted_species.localeCompare(b.predicted_species);
    }
  }
  switch (true) {
    case a.predicted_species === Undetected:
      return 1;
    case b.predicted_species === Undetected:
      return -1;
    default:
      return a.predicted_species.localeCompare(b.predicted_species);
  }
}

export function fetchAnnotations(
  sessionID: string
): Promise<Array<Annotation>> {
  interface AnnotationsResponse {
    status: string;
    annotations: Array<Annotation>;
  }

  return fetch("/api/v1/annotations", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: AnnotationsResponse) => data.annotations);
}

export function submitAnnotations(
  sessionID: string,
  annotations: Array<Annotation>
): Promise<string> {
  const annotationsJSON = JSON.stringify(annotations);
  return fetch("/api/v1/annotations", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      SessionID: sessionID,
    },
    body: annotationsJSON,
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => data.status);
}
