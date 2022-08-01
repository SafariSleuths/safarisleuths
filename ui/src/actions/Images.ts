import { failIfNotOk, StatusResponse } from "./StatusResponse";

export function deleteImages(
  collectionID: string,
  images: Array<string>
): Promise<void> {
  return fetch(`/api/v1/images?collectionID=${collectionID}`, {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(images),
  })
    .then((resp) => resp.json())
    .then((data: StatusResponse) => failIfNotOk(data));
}

export function uploadImages(
  collectionID: string,
  files: FileList | null
): Promise<Array<string>> {
  interface PostImagesResponse extends StatusResponse {
    uploaded: Array<string>;
  }

  if (files === null) {
    return Promise.resolve([]);
  }

  const data = new FormData();
  for (let i = 0; i < files.length; i++) {
    data.append(files[i].name, files[i]);
  }
  return fetch(`/api/v1/images?collectionID=${collectionID}`, {
    method: "POST",
    body: data,
  })
    .then((resp) => resp.json())
    .then((data: PostImagesResponse) => {
      failIfNotOk(data);
      return data.uploaded;
    });
}

export function listImages(collectionID: string): Promise<Array<string>> {
  interface ListImagesResponse extends StatusResponse {
    images: Array<string>;
  }

  return fetch(`/api/v1/images?collectionID=${collectionID}`, { method: "GET" })
    .then((resp) => resp.json())
    .then((data: ListImagesResponse) => {
      failIfNotOk(data);
      return data.images;
    });
}
