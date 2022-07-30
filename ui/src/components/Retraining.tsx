import { Box, Stack } from "@mui/material";
import React from "react";
import { fetchRetrainLogs, RetrainEventLog } from "../actions/RetrainingLogs";
import { RetrainingLogsTable } from "./RetrainingLogsTable";
import { RetrainingButtons } from "./RetrainingButtons";
import { fetchRetrainStatus, RetrainJob } from "../actions/RetrainJob";
import { RetrainImagesDisplay } from "./RetrainImagesDisplay";

export function Retraining(props: { collectionID: string }) {
  const [retrainJob, setRetrainJob] = React.useState<RetrainJob | undefined>(
    undefined
  );
  const [retrainLogs, setRetrainLogs] = React.useState<Array<RetrainEventLog>>(
    []
  );

  const firstUpdate = React.useRef(true);
  React.useEffect(() => {
    if (firstUpdate.current || retrainJob === undefined) {
      fetchRetrainStatus(props.collectionID).then((job) => setRetrainJob(job));
      fetchRetrainLogs(props.collectionID).then((logs) => setRetrainLogs(logs));
      firstUpdate.current = false;
    }
    const interval = setInterval(() => {
      if (retrainJob?.status == "completed") {
        clearInterval(interval);
      }
      fetchRetrainStatus(props.collectionID).then((job) => setRetrainJob(job));
      fetchRetrainLogs(props.collectionID).then((logs) => setRetrainLogs(logs));
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
        collectionID={props.collectionID}
        job={retrainJob}
        setJob={setRetrainJob}
        setLogs={setRetrainLogs}
      />
      <RetrainingStatus job={retrainJob} />
      <RetrainingLogsTable logs={retrainLogs} />
      <RetrainImagesDisplay collectionID={props.collectionID} />
    </Stack>
  );
}

function RetrainingStatus(props: { job: RetrainJob | undefined }) {
  if (props.job === undefined) {
    return <Box />;
  }
  return (
    <Box>
      <h3>Retrain Status: {props.job.status.toUpperCase()}</h3>
    </Box>
  );
}
