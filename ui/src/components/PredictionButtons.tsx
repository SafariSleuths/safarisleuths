import { Annotation, compareAnnotations } from "../actions/Annotations";
import { Button, ButtonGroup, Tooltip } from "@mui/material";
import { Download } from "@mui/icons-material";
import React from "react";
import { fetchPredictions } from "../actions/Predictions";

export function PredictionButtons(props: {
  collectionID: string;
  setShowLoading: (v: boolean) => void;
  setAnnotations: (v: Array<Annotation>) => void;
  jsonDownloadUrl: string | undefined;
}) {
  const getPredictions = () =>
    fetchAndSortPredictions(
      props.collectionID,
      props.setShowLoading,
      props.setAnnotations
    );

  return (
    <ButtonGroup>
      <Tooltip title={"Compute predictions for the uploaded images."}>
        <Button onClick={getPredictions}>Compute Results</Button>
      </Tooltip>
      <Tooltip title={"Download all annotations in json format."}>
        <span>
          <Button
            href={props.jsonDownloadUrl || "#"}
            disabled={props.jsonDownloadUrl === undefined}
            download={"results.json"}
          >
            <Download /> Annotations
          </Button>
        </span>
      </Tooltip>
    </ButtonGroup>
  );
}

function fetchAndSortPredictions(
  collectionID: string,
  setShowLoading: (v: boolean) => void,
  setAnnotations: (v: Array<Annotation>) => void
) {
  setShowLoading(true);
  fetchPredictions(collectionID).then((annotations) => {
    annotations.sort(compareAnnotations);
    setAnnotations(annotations);
    setShowLoading(false);
  });
}
