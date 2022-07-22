import React, { useEffect, useRef, useState } from "react";
import {
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  FormControl,
  Grid,
  ImageList,
  ImageListItem,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
} from "@mui/material";

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

function SessionSelect(props: {
  sessionID: string;
  setSessionID: (v: string) => void;
}) {
  const [sessions, setSessions] = useState<Array<Session> | undefined>(
    undefined
  );

  useEffect(() => {
    if (sessions === undefined) {
      getSessions().then((data) => setSessions(data.sessions));
    }
  });

  const [newSession, setNewSession] = React.useState("");
  const [canSubmit, setCanSubmit] = React.useState(false);

  return (
    <Grid marginTop={2} container>
      <Grid item xs={3}>
        <h4>Choose an existing session:</h4>
        <InputLabel id="session">Session</InputLabel>
        <Select
          size={"small"}
          value={sessions !== undefined ? props.sessionID : ""}
          label="Session"
          id="session"
          onChange={(e) => props.setSessionID(e.target.value)}
        >
          {sessions?.map((session) => (
            <MenuItem key={session.id} value={session.id}>
              {session.name}
            </MenuItem>
          ))}
        </Select>
      </Grid>
      <Grid item xs={9}>
        <h4>Create a new session:</h4>
        <Grid container spacing={1}>
          <Grid item>
            <TextField
              label={"Name"}
              size={"small"}
              onChange={(e) => {
                setNewSession(e.target.value);
                if (e.target.value !== "") {
                  setCanSubmit(true);
                }
              }}
            />
          </Grid>
          <Grid item>
            <Button
              variant={"outlined"}
              disabled={!canSubmit}
              onClick={() => {
                putSession(newSession).then((resp) => {
                  setSessions([...(sessions || []), resp.session]);
                  props.setSessionID(resp.session.id);
                });
              }}
            >
              Submit
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
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

function deleteFiles(fileNames: Array<string>): Promise<Array<string>> {
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
    .then((data) => data["images"] as Array<string>);
}

interface Session {
  id: string;
  name: string;
}

interface GetSessionsResponse {
  status: string;
  sessions: Array<Session>;
}

function getSessions(): Promise<GetSessionsResponse> {
  return fetch("/api/v1/sessions", {
    method: "GET",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}

interface PutSessionResponse {
  session: Session;
}

function putSession(name: string): Promise<PutSessionResponse> {
  return fetch("/api/v1/sessions", {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name: name }),
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
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
      "Content-Type": "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}
