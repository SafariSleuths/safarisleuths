export const StatusOk = "ok";

export interface StatusResponse {
  status: string;
  error_name: string;
  error_reason: string;
}

export function failIfNotOk(resp: StatusResponse): void {
  if (resp.status != StatusOk) {
    throw `${resp.error_name}: ${resp.error_reason}`;
  }
}
