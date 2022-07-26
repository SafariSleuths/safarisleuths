import {
  Box,
  Button,
  ButtonGroup,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
import React, { useState } from "react";
import { Annotation } from "./Predictions";
import { ImageModal } from "./ImageModal";

interface RetrainJob {
  session_id: string;
  created_at: number;
  status: string;
}

interface RetrainEventLog {
  session_id: string;
  created_at: number;
  message: string;
}

export function ViewRetraining(props: { sessionID: string }) {
  const [retrainJob, setRetrainJob] = React.useState<RetrainJob | undefined>(
    undefined
  );
  const [retrainLogs, setRetrainLogs] = React.useState<Array<RetrainEventLog>>(
    []
  );

  const firstUpdate = React.useRef(true);
  React.useEffect(() => {
    if (firstUpdate.current || retrainJob === undefined) {
      fetchRetrainJob(props.sessionID).then((job) => setRetrainJob(job));
      fetchRetrainLogs(props.sessionID).then((logs) => setRetrainLogs(logs));
      firstUpdate.current = false;
    }
    const interval = setInterval(() => {
      if (retrainJob?.status == "completed") {
        clearInterval(interval);
      }
      fetchRetrainJob(props.sessionID).then((job) => setRetrainJob(job));
      fetchRetrainLogs(props.sessionID).then((logs) => setRetrainLogs(logs));
    }, 5000);
    return () => clearInterval(interval);
  });

  return (
    <Stack spacing={2}>
      <p>
        Retrain the individual animal classifiers using images reviewed in the
        Prediction Results tab.
      </p>
      <RetrainingButtons
        sessionID={props.sessionID}
        job={retrainJob}
        setJob={setRetrainJob}
        setLogs={setRetrainLogs}
      />
      <ViewRetrainingStatus job={retrainJob} />
      <ViewRetrainingLogs logs={retrainLogs} />
      <ViewRetrainAnnotations sessionID={props.sessionID} />
    </Stack>
  );
}

function RetrainingButtons(props: {
  sessionID: string;
  job: RetrainJob | undefined;
  setJob: (v: RetrainJob | undefined) => void;
  setLogs: (v: Array<RetrainEventLog>) => void;
}) {
  const canStart =
    props.job?.status === "completed" ||
    props.job?.status === "not started" ||
    props.job?.status === "aborted";

  const canAbort = !canStart;
  const canClear = canStart;

  return (
    <ButtonGroup>
      <Button
        disabled={!canStart}
        onClick={() =>
          startRetraining(props.sessionID).then(() => {
            props.setJob(undefined);
            props.setLogs([]);
          })
        }
      >
        Start Retraining
      </Button>
      <Button
        disabled={!canAbort}
        onClick={() => abortRetraining(props.sessionID)}
      >
        Abort Retraining
      </Button>
      <Button
        disabled={!canClear}
        onClick={() =>
          clearRetraining(props.sessionID).then(() => {
            props.setJob(undefined);
            props.setLogs([]);
          })
        }
      >
        Clear Status
      </Button>
    </ButtonGroup>
  );
}

function ViewRetrainingStatus(props: { job: RetrainJob | undefined }) {
  if (props.job === undefined) {
    return <Box />;
  }
  return (
    <Box>
      <h3>Retrain Status: {props.job.status.toUpperCase()}</h3>
    </Box>
  );
}

function ViewRetrainingLogs(props: { logs: Array<RetrainEventLog> }) {
  let content = (
    <Table size={"small"}>
      <TableBody>
        {props.logs.map((log, i) => (
          <TableRow key={i}>
            <TableCell align="left">
              {new Date(log.created_at * 1000).toLocaleString()}
            </TableCell>
            <TableCell align="left">{log.message}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  if (props.logs.length === 0) {
    content = (
      <Box>
        <pre>Nothing here 🤷</pre>
      </Box>
    );
  }
  return (
    <Stack>
      <h3>Retraining Logs:</h3>
      {content}
    </Stack>
  );
}

function ViewRetrainAnnotations(props: { sessionID: string }) {
  const [annotations, setAnnotations] = React.useState<
    Array<Annotation> | undefined
  >(undefined);

  const loaded = React.useRef(false);
  React.useEffect(() => {
    if (!loaded.current) {
      fetchAnnotations(props.sessionID).then((new_annotations) =>
        setAnnotations(new_annotations.filter((a) => a.accepted))
      );
      loaded.current = true;
    }
  });

  if (annotations == undefined) {
    return (
      <Box>
        No images can be used for retraining. Please review images in the
        predictions tab.
      </Box>
    );
  }

  return (
    <Box>
      <h3>Images included in retraining</h3>
      <ImageList cols={5} gap={6}>
        {annotations
          .map((annotation) => ({
            file_name: annotation.cropped_file_name || "",
            name: annotation.predicted_name || "",
            species: annotation.predicted_species || "",
          }))
          .filter((v) => v.file_name != "")
          .filter((v) => v.name != "")
          .filter((v) => v.species != "")
          .map((v, i) => (
            <RetrainingImageItem
              key={i}
              cropped_file_name={v.file_name}
              predicted_name={v.name}
              predicted_species={v.species.replace("_", " ")}
            />
          ))}
      </ImageList>
    </Box>
  );
}

function RetrainingImageItem(props: {
  cropped_file_name: string;
  predicted_name: string;
  predicted_species: string;
}) {
  const [openImageModal, setOpenImageModal] = useState(false);
  const title = (
    <Box>
      Name: {props.predicted_name}
      <br />
      Species: {props.predicted_species}
    </Box>
  );
  return (
    <ImageListItem>
      <img
        style={{ height: 300, width: 300 }}
        src={props.cropped_file_name}
        srcSet={props.cropped_file_name}
        alt={props.cropped_file_name}
        loading="lazy"
        onClick={() => setOpenImageModal(true)}
      />
      <ImageModal
        src={props.cropped_file_name}
        alt={props.cropped_file_name}
        open={openImageModal}
        setOpen={setOpenImageModal}
      />
      <ImageListItemBar position={"below"} subtitle={title} />
    </ImageListItem>
  );
}

interface GetRetrainJobResponse {
  status: string;
  job: RetrainJob;
}

function fetchRetrainJob(sessionID: string): Promise<RetrainJob> {
  return fetch("/api/v1/retrain_job", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainJobResponse) => data.job);
}

interface GetRetrainLogsResponse {
  status: string;
  logs: Array<RetrainEventLog>;
}

function fetchRetrainLogs(sessionID: string): Promise<Array<RetrainEventLog>> {
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

interface GetRetrainResponse {
  status: string;
}

function startRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/retrain", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainResponse) => data.status);
}

function abortRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/abort_retrain_job", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainResponse) => data.status);
}

function clearRetraining(sessionID: string): Promise<string> {
  return fetch("/api/v1/retrain_job", {
    method: "DELETE",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetRetrainResponse) => data.status);
}

interface GetAnnotationsResponse {
  status: string;
  annotations: Array<Annotation>;
}

function fetchAnnotations(sessionID: string): Promise<Array<Annotation>> {
  return fetch("/api/v1/annotations", {
    method: "GET",
    headers: {
      Accept: "application/json",
      SessionID: sessionID,
    },
  })
    .then((resp) => resp.json())
    .then((data: GetAnnotationsResponse) => data.annotations);
}
