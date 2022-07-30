import { StatusResponse } from "./StatusResponse";

export interface RetrainJob {
  session_id: string;
  created_at: number;
  status: string;
}

export function fetchRetrainJob(sessionID: string): Promise<RetrainJob> {
  interface GetRetrainJobResponse {
    status: string;
    job: RetrainJob;
  }

  return fetch("/api/v1/retrain_job", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainJobResponse) => data.job);
}

export function startRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/retrain", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => data.status);
}

export function abortRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/abort_retrain_job", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => data.status);
}

export function clearRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/retrain_job", {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => data.status);
}
