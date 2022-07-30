export interface RetrainEventLog {
  session_id: string;
  created_at: number;
  message: string;
}

interface GetRetrainLogsResponse {
  status: string;
  logs: Array<RetrainEventLog>;
}

export function fetchRetrainLogs(
  sessionID: string
): Promise<Array<RetrainEventLog>> {
  return fetch("/api/v1/retrain_logs", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainLogsResponse) => data.logs);
}
