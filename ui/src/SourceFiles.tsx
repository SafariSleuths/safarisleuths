import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  ImageList,
  ImageListItem,
  Stack,
} from "@mui/material";
import { SessionSelect } from "./SessionSelect";

export function SourceFiles(props: {
  sessionID: string;
  setSessionID: (v: string) => void;
}) {
  const [uploadedFiles, setUploadedFiles] = useState<Array<string> | undefined>(
    undefined
  );

  useEffect(() => {
    if (uploadedFiles === undefined) {
      listImages(props.sessionID).then((data) => setUploadedFiles(data.images));
    }
  });

  return (
    <Stack spacing={2}>
      <p>
        Upload new photos to use for predictions. For the demo, the upload
        button is disabled, but you will be able to upload whatever amount of
        images files here.
      </p>
      <SessionSelect
        sessionID={props.sessionID}
        setSessionID={props.setSessionID}
        setUploadedFiles={setUploadedFiles}
      />
      <UploadForm
        sessionID={props.sessionID}
        uploadedFiles={uploadedFiles}
        setUploadedFiles={setUploadedFiles}
      />

      <Stack alignItems={"center"}>
        <ImageList cols={5} gap={12}>
          {(uploadedFiles || []).map((src, i) => (
            <ImageListItem key={i}>
              <img src={src} srcSet={src} alt={src} loading="lazy" />
              <Button
                fullWidth
                onClick={() =>
                  deleteFiles(props.sessionID, [src]).then(() => {
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

function UploadForm(props: {
  sessionID: string;
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
          disabled={selectedFiles == null}
          onClick={() => {
            setShowLoading(true);
            uploadImages(props.sessionID, selectedFiles).then((uploaded) => {
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

interface DeleteImagesResponse {
  status: string;
}

function deleteFiles(
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

function uploadImages(
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

interface ImagesResponse {
  status: string;
  images: Array<string>;
}

function listImages(sessionID: string): Promise<ImagesResponse> {
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
