import { failIfNotOk, StatusResponse } from "./StatusResponse";

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
  collectionID: string
): Promise<Array<Annotation>> {
  interface AnnotationsResponse extends StatusResponse {
    annotations: Array<Annotation>;
  }

  return fetch(`/api/v1/annotations?collectionID=${collectionID}`, {
    method: "GET",
    headers: { Accept: "application/json" },
  })
    .then((resp) => resp.json())
    .then((data: AnnotationsResponse) => {
      failIfNotOk(data);
      return data.annotations;
    });
}

export function submitAnnotations(
  collectionID: string,
  annotations: Array<Annotation>
): Promise<void> {
  return fetch(`/api/v1/annotations?collectionID=${collectionID}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(annotations),
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => failIfNotOk(data));
}
