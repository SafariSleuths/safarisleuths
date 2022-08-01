import { RetrainEventLog } from "../actions/RetrainingLogs";
import { Button, ButtonGroup } from "@mui/material";
import React from "react";
import {
  abortRetraining,
  clearRetraining,
  retrainClassifier,
  retrainEmbeddings,
  RetrainJob,
} from "../actions/RetrainJob";

export function RetrainingButtons(props: {
  collectionID: string;
  job: RetrainJob | undefined;
  setJob: (v: RetrainJob | undefined) => void;
  setLogs: (v: Array<RetrainEventLog>) => void;
}) {
  const canStart =
    props.job?.status === "completed" ||
    props.job?.status === "not started" ||
    props.job?.status === "aborted";

  return (
    <ButtonGroup>
      <Button
        disabled={!canStart}
        onClick={() =>
          retrainEmbeddings(props.collectionID).then(() => {
            props.setJob(undefined);
            props.setLogs([]);
          })
        }
      >
        Start Retraining
      </Button>
      <Button
        disabled={!canStart}
        onClick={() =>
          retrainClassifier(props.collectionID).then(() => {
            props.setJob(undefined);
            props.setLogs([]);
          })
        }
      >
        Classifier Only <small>(faster)</small>
      </Button>
      <Button
        disabled={!canStart}
        onClick={() =>
          clearRetraining(props.collectionID).then(() => {
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
