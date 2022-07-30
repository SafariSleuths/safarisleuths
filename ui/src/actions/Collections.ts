import { failIfNotOk, StatusResponse } from "./StatusResponse";

export interface Collection {
  id: string;
  name: string;
}

export function getCollections(): Promise<Array<Collection>> {
  interface GetCollectionsResponse extends StatusResponse {
    collections: Array<Collection>;
  }

  return fetch("/api/v1/collections", {
    method: "GET",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((respBody) => respBody.json())
    .then((data: GetCollectionsResponse) => {
      failIfNotOk(data);
      return data.collections;
    });
}

export function postCollection(name: string): Promise<Collection> {
  interface PostCollectionResponse extends StatusResponse {
    collection: Collection;
  }

  return fetch("/api/v1/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: name }),
  })
    .then((resp) => resp.json())
    .then((data: PostCollectionResponse) => {
      failIfNotOk(data);
      return data.collection;
    });
}
