import {
  Box,
  Button,
  List,
  ListItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
import React from "react";
import { Annotation } from "./Predictions";

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

  const [retrainAnnotations, setRetrainAnnotations] = React.useState<
    Array<Annotation>
  >([]);

  const firstUpdate = React.useRef(true);
  React.useEffect(() => {
    if (firstUpdate.current) {
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
    <Box>
      <Button onClick={() => startRetraining(props.sessionID)}>
        Start Retraining
      </Button>
      <ViewRetrainAnnotations sessionID={props.sessionID} />
      <RetrainingLogs logs={retrainLogs} />
    </Box>
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

  return (
    <Box>
      <List>
        {annotations?.map((annotation, i) => (
          <ListItem key={i}>{annotation.cropped_file_name}</ListItem>
        ))}
      </List>
    </Box>
  );
}

function RetrainingLogs(props: { logs: Array<RetrainEventLog> }) {
  if (props.logs.length == 0) {
    return <Box />;
  }

  return (
    <Stack>
      <h2>Retraining Logs</h2>
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
    </Stack>
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
