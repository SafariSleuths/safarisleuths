import { failIfNotOk, StatusResponse } from "./StatusResponse";

export interface RetrainEventLog {
  collection_id: string;
  created_at: number;
  message: string;
}

export function fetchRetrainLogs(
  collectionID: string
): Promise<Array<RetrainEventLog>> {
  interface GetRetrainLogsResponse extends StatusResponse {
    logs: Array<RetrainEventLog>;
  }

  return fetch(`/api/v1/retrain/logs?collectionID=${collectionID}`, {
    method: "GET",
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainLogsResponse) => {
      failIfNotOk(data);
      return data.logs;
    });
}
