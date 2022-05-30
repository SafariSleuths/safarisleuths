import React, { useEffect, useState } from "react";
import { Button, CircularProgress, FormControl, Stack } from "@mui/material";
import { ApiResponse, PredictRequest, Status } from "./ApiRequest";

export function UploadMenu(props: { sessionID: string }) {
  const [uploadedFiles, setUploadedFiles] = useState<Array<string> | undefined>(
    undefined
  );

  useEffect(() => {
    if (uploadedFiles === undefined) {
      fetchListFiles({}).then((data) => setUploadedFiles(data.images));
    }
  });

  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  const [showLoading, setShowLoading] = useState(false);
  return (
    <Stack spacing={2}>
      <h2>Source Files</h2>
      <FormControl>
        <input
          multiple={true}
          accept={"image/jpeg,image/png"}
          type={"file"}
          onChange={(e) => setSelectedFiles(e.target.files)}
        />
        <Button
          disabled={selectedFiles == null}
          onClick={() => {
            setShowLoading(true);
            uploadFiles(selectedFiles).then((uploaded) => {
              setShowLoading(false);
              setSelectedFiles(null);
              setUploadedFiles([...uploaded, ...(uploadedFiles ?? [])]);
            });
          }}
        >
          Upload Photos
        </Button>
      </FormControl>
      <Stack>
        {showLoading ? <CircularProgress /> : <div />}
        {uploadedFiles?.map((src, i) => (
          <Stack alignItems={"center"} key={i}>
            <p>{src.slice(src.lastIndexOf("/") + 1)}</p>
            <img src={src} alt={src} width={250} />
            <Button
              style={{ width: 250 }}
              onClick={() =>
                deleteFiles([src]).then(() => {
                  setUploadedFiles(uploadedFiles?.filter((n) => n != src));
                })
              }
            >
              Delete
            </Button>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}

function deleteFiles(fileNames: Array<string>): Promise<Array<string>> {
  console.log();
  return fetch("/api/v1/delete_files", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ files: fileNames }),
  })
    .then((resp) => resp.json())
    .then((data) => data["deleted"] as Array<string>);
}

function uploadFiles(files: FileList | null): Promise<Array<string>> {
  if (files === null) {
    return Promise.resolve([]);
  }

  const data = new FormData();
  for (let i = 0; i < files.length; i++) {
    data.append(files[i].name, files[i]);
  }
  return fetch("/api/v1/upload_files", {
    method: "POST",
    body: data,
  })
    .then((resp) => resp.json())
    .then((data) => data["images"] as Array<string>);
}

interface ListFilesRequest {}

interface ListFilesResponse {
  status: Status;
  images: Array<string>;
}

function fetchListFiles(req: ListFilesRequest): Promise<ListFilesResponse> {
  return fetch("/api/v1/list_files", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(req),
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}
