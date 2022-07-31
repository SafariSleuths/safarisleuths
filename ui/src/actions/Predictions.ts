import { Annotation } from "./Annotations";
import { failIfNotOk, StatusResponse } from "./StatusResponse";

export function fetchPredictions(
  collectionID: string
): Promise<Array<Annotation>> {
  interface PredictionResponse extends StatusResponse {
    annotations: Array<Annotation>;
  }

  return fetch(`/api/v1/predictions?collectionID=${collectionID}`, {
    method: "POST",
  })
    .then((resp) => resp.json())
    .then((data: PredictionResponse) => {
      failIfNotOk(data);
      return data.annotations;
    });
}
