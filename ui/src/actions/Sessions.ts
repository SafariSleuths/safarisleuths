export interface Session {
  id: string;
  name: string;
}

export interface GetSessionsResponse {
  status: string;
  sessions: Array<Session>;
}

export function getSessions(): Promise<Array<Session>> {
  return fetch("/api/v1/sessions", {
    method: "GET",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((respBody) => respBody.json())
    .then((respData: GetSessionsResponse) => respData.sessions);
}

export interface PutSessionResponse {
  status: string;
  session: Session;
}

export function putSession(name: string): Promise<Session> {
  return fetch("/api/v1/sessions", {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: name }),
  })
    .then((resp) => resp.json())
    .then((data: PutSessionResponse) => data.session);
}
