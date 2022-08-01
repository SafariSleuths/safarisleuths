import React, { useEffect, useState } from "react";
import { Box, CircularProgress, ImageList, Paper, Stack } from "@mui/material";

import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";

import { ExpandMore } from "@mui/icons-material";

import {
  fetchAnnotations,
  Annotation,
  compareAnnotations,
  Undetected,
} from "../actions/Annotations";
import { SummaryTable } from "./SummaryTable";
import { PredictionButtons } from "./PredictionButtons";
import { AnnotatedImagesDisplay } from "./AnnotatedImagesDisplay";

export function PredictionResults(props: { collectionID: string }) {
  const [annotations, setAnnotations] = useState<Array<Annotation> | undefined>(
    undefined
  );

  const [showLoading, setShowLoading] = useState(false);
  const [predictionError, setPredictionError] = useState("");

  const jsonDownloadUrl = useJsonDownloadUrl(annotations);
  const annotationsByName: Map<string, Array<Annotation>> = (
    annotations || ([] as Array<Annotation>)
  ).reduce(
    (a, b) => a.set(b.predicted_name, [...(a.get(b.predicted_name) || []), b]),
    new Map<string, Array<Annotation>>()
  );

  const updateAnnotations = (updates: Array<Annotation>) => {
    const annotationsById: Map<number, Annotation> = (
      annotations || ([] as Array<Annotation>)
    ).reduce((a, b) => a.set(b.id, b), new Map<number, Annotation>());
    updates.forEach((annotation) =>
      annotationsById.set(annotation.id, annotation)
    );
    const newAnnotations = Array.from(annotationsById.values());
    setAnnotations(newAnnotations);
  };

  React.useEffect(() => {
    if (annotations === undefined) {
      fetchAnnotations(props.collectionID).then((newAnnotations) =>
        setAnnotations(newAnnotations.sort(compareAnnotations))
      );
    }
  });

  return (
    <Stack spacing={2}>
      <p>
        Compute predictions and review results. Once images have been reviewed,
        they can be used to fine-tuning the model for future predictions.
      </p>
      <PredictionButtons
        collectionID={props.collectionID}
        setAnnotations={setAnnotations}
        setShowLoading={setShowLoading}
        jsonDownloadUrl={jsonDownloadUrl}
        setPredictionError={setPredictionError}
      />
      <DisplayAnnotations
        collectionID={props.collectionID}
        showLoading={showLoading}
        predictionError={predictionError}
        updateAnnotations={updateAnnotations}
        annotationsByName={annotationsByName}
      />
    </Stack>
  );
}

function DisplayAnnotations(props: {
  collectionID: string;
  showLoading: boolean;
  predictionError: string;
  updateAnnotations: (updates: Array<Annotation>) => void;
  annotationsByName: Map<string, Array<Annotation>>;
}) {
  if (props.predictionError != "") {
    return <Box>{props.predictionError}</Box>;
  }

  if (props.showLoading) {
    return (
      <Box alignContent={"center"} width={"100%"}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Stack spacing={4} hidden={props.showLoading}>
      <Paper>
        <Box margin={2}>
          <h3>Summary</h3>
          <SummaryTable annotationsByName={props.annotationsByName} />
        </Box>
      </Paper>
      <AnimalBreakdown
        collectionID={props.collectionID}
        name={Undetected}
        subtitle={"We could not detect or label the animal in these images."}
        annotations={props.annotationsByName.get(Undetected) || []}
        setAnnotations={props.updateAnnotations}
      />
      {Array.from(props.annotationsByName)
        .filter(([name, _]) => name !== Undetected)
        .map(([name, annotations]) => (
          <AnimalBreakdown
            collectionID={props.collectionID}
            key={name}
            name={name}
            subtitle={""}
            annotations={annotations}
            setAnnotations={props.updateAnnotations}
          />
        ))}
    </Stack>
  );
}

function AnimalBreakdown(props: {
  collectionID: string;
  name: string;
  annotations: Array<Annotation>;
  setAnnotations: (v: Array<Annotation>) => void;
  subtitle: string;
}) {
  if (props.annotations.length === 0) {
    return <Box />;
  }

  const pendingReview = props.annotations.filter((a) => a.accepted).length;
  let title = `Animal ID: ${props.name} (${pendingReview}/${props.annotations.length} reviewed)`;
  if (props.name === Undetected) {
    title = `None detected (${pendingReview}/${props.annotations.length} reviewed)`;
  }

  const species = props.annotations[0].predicted_species.replace("_", " ");

  return (
    <Box>
      <Accordion defaultExpanded={true}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <h3>{title}</h3>
        </AccordionSummary>
        <AccordionDetails>
          <Box>
            Species: <i>{species}</i>
          </Box>
          <AnimalImageList
            collectionID={props.collectionID}
            annotations={props.annotations}
            setAnnotations={props.setAnnotations}
          />
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}

function AnimalImageList(props: {
  annotations: Array<Annotation>;
  setAnnotations: (v: Array<Annotation>) => void;
  collectionID: string;
}) {
  props.annotations.sort((a, b) => {
    let a_score = 0;
    let b_score = 0;
    if (a.accepted) {
      a_score = 100;
    }
    if (b.accepted) {
      b_score = 100;
    }
    if (a.ignored) {
      a_score = 200;
    }
    if (b.ignored) {
      b_score = 200;
    }
    if (a_score === b_score) {
      return a.predicted_name.localeCompare(b.predicted_name);
    }
    return a_score - b_score;
  });

  return (
    <ImageList cols={3} gap={12}>
      {props.annotations.map((annotation, i) => (
        <AnnotatedImagesDisplay
          collectionID={props.collectionID}
          key={i}
          annotation={annotation}
          setAnnotation={(v: Annotation) => {
            props.setAnnotations([v]);
          }}
        />
      ))}
    </ImageList>
  );
}

function useJsonDownloadUrl(
  annotations: Array<Annotation> | undefined
): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const data = JSON.stringify({ annotations: annotations });
  useEffect(() => {
    if (annotations === undefined) {
      return;
    }

    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    setUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [data, annotations]);
  return url;
}
