import { failIfNotOk, StatusResponse } from "./StatusResponse";

export interface RetrainJob {
  collection_id: string;
  created_at: number;
  status: string;
}

export function fetchRetrainStatus(collectionID: string): Promise<RetrainJob> {
  interface GetRetrainJobResponse extends StatusResponse {
    job: RetrainJob;
  }

  return fetch(`/api/v1/retrain/status?collectionID=${collectionID}`, {
    method: "GET",
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainJobResponse) => {
      failIfNotOk(data);
      return data.job;
    });
}

export function retrainClassifier(collectionID: string): Promise<void> {
  return fetch(`/api/v1/retrain/classifier?collectionID=${collectionID}`, {
    method: "POST",
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => failIfNotOk(data));
}

export function retrainEmbeddings(collectionID: string): Promise<void> {
  return fetch(`/api/v1/retrain/embeddings?collectionID=${collectionID}`, {
    method: "POST",
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => failIfNotOk(data));
}

export function abortRetraining(collectionID: string): Promise<void> {
  return fetch(`/api/v1/retrain/abort?collectionID=${collectionID}`, {
    method: "POST",
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => failIfNotOk(data));
}

export function clearRetraining(collectionID: string): Promise<string> {
  return fetch(`/api/v1/retrain/status?collectionID=${collectionID}`, {
    method: "DELETE",
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => data.status);
}
