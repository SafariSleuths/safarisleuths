import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  Grid,
  ImageList,
  ImageListItem,
  InputLabel,
  MenuItem,
  Select,
  Stack,
} from "@mui/material";

export function SourceFiles(props: { sessionID: string }) {
  const [uploadedFiles, setUploadedFiles] = useState<Array<string> | undefined>(
    undefined
  );

  useEffect(() => {
    if (uploadedFiles === undefined) {
      fetchListFiles({ session_id: props.sessionID }).then((data) =>
        setUploadedFiles(data.images)
      );
    }
  });

  return (
    <Stack spacing={2}>
      <p>Upload new photos to use for predictions.</p>
      <SessionSelect />
      <UploadForm
        uploadedFiles={uploadedFiles}
        setUploadedFiles={setUploadedFiles}
      />

      <Stack alignItems={"center"}>
        <ImageList cols={5} gap={12}>
          {(uploadedFiles || []).map((src, i) => (
            <ImageListItem key={i}>
              <img src={src} srcSet={src} alt={src} loading="lazy" />
              <Button
                disabled
                fullWidth
                onClick={() =>
                  deleteFiles([src]).then(() => {
                    setUploadedFiles(uploadedFiles?.filter((n) => n != src));
                  })
                }
              >
                Delete
              </Button>
            </ImageListItem>
          ))}
        </ImageList>
      </Stack>
    </Stack>
  );
}

function SessionSelect() {
  return (
    <Box marginTop={2}>
      <InputLabel id="session">Session</InputLabel>
      <Select size={"small"} value="Demo" label="Session" id="session">
        <MenuItem value="Demo">Demo</MenuItem>
      </Select>
    </Box>
  );
}

function UploadForm(props: {
  uploadedFiles: Array<string> | undefined;
  setUploadedFiles: (value: Array<string> | undefined) => void;
}) {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showLoading, setShowLoading] = useState(false);

  return (
    <Box marginTop={2}>
      <FormControl>
        <input
          ref={inputRef}
          multiple={true}
          accept={"image/jpeg,image/png"}
          type={"file"}
          onChange={(e) => setSelectedFiles(e.target.files)}
        />
        <Button
          disabled={selectedFiles == null || true}
          onClick={() => {
            setShowLoading(true);
            uploadFiles(selectedFiles).then((uploaded) => {
              setShowLoading(false);
              setSelectedFiles(null);
              props.setUploadedFiles([
                ...uploaded,
                ...(props.uploadedFiles ?? []),
              ]);
            });
            if (inputRef.current != null) {
              inputRef.current.value = "";
            }
          }}
        >
          Upload Photos
        </Button>
      </FormControl>
      <Box hidden={!showLoading}>
        <CircularProgress />{" "}
      </Box>
    </Box>
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

interface ListFilesRequest {
  session_id: string;
}

interface ListFilesResponse {
  status: string;
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
