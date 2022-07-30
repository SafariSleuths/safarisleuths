import { RetrainEventLog } from "../actions/RetrainingLogs";
import { Button, ButtonGroup } from "@mui/material";
import React from "react";
import {
  abortRetraining,
  clearRetraining,
  RetrainJob,
  startRetraining,
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

  const canAbort = !canStart;
  const canClear = canStart;

  return (
    <ButtonGroup>
      <Button
        disabled={!canStart}
        onClick={() =>
          startRetraining(props.collectionID).then(() => {
            props.setJob(undefined);
            props.setLogs([]);
          })
        }
      >
        Start Retraining
      </Button>
      <Button
        disabled={!canAbort}
        onClick={() => abortRetraining(props.collectionID)}
      >
        Abort Retraining
      </Button>
      <Button
        disabled={!canClear}
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
