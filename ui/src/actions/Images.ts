interface DeleteImagesResponse {
  status: string;
}

export function deleteImages(
  sessionID: string,
  images: Array<string>
): Promise<string> {
  return fetch("/api/v1/images", {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      SessionID: sessionID,
    },
    body: JSON.stringify({ images: images }),
  })
    .then((resp) => resp.json())
    .then((data: DeleteImagesResponse) => data.status);
}

interface PostImagesResponse {
  status: string;
  uploaded: Array<string>;
}

export function uploadImages(
  sessionID: string,
  files: FileList | null
): Promise<Array<string>> {
  if (files === null) {
    return Promise.resolve([]);
  }

  const data = new FormData();
  for (let i = 0; i < files.length; i++) {
    data.append(files[i].name, files[i]);
  }
  return fetch("/api/v1/images", {
    method: "POST",
    headers: { SessionID: sessionID },
    body: data,
  })
    .then((resp) => resp.json())
    .then((data: PostImagesResponse) => data.uploaded);
}

interface ListImagesResponse {
  status: string;
  images: Array<string>;
}

export function listImages(sessionID: string): Promise<ListImagesResponse> {
  return fetch("/api/v1/images", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}
