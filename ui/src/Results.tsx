import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";

import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";

import { Download, ExpandMore, Upload } from "@mui/icons-material";

export function Results(props: { sessionID: string }) {
  const [predictionResponse, setPredictionResponse] = useState<
    PredictionResponse | undefined
  >(undefined);

  const [showLoading, setShowLoading] = useState(false);

  function getPredictions() {
    setPredictionResponse(undefined);
    setShowLoading(true);
    fetchPredictions({ session_id: props.sessionID }).then((data) => {
      setPredictionResponse(data);
      setShowLoading(false);
    });
  }

  const jsonDownloadUrl = useJsonDownloadUrl(predictionResponse?.annotations);

  const annotationsByName = (predictionResponse?.annotations || []).reduce(
    (a, b) => a.set(b.name, [...(a.get(b.name) || []), b]),
    new Map<string, Array<Annotation>>()
  );

  return (
    <Stack spacing={2}>
      <h2>Prediction Results</h2>
      <ButtonGroup variant={"text"}>
        <Button onClick={getPredictions}>Compute Results</Button>
        <Button
          href={jsonDownloadUrl || "#"}
          disabled={jsonDownloadUrl === undefined}
          download={"results.json"}
        >
          <Download /> Annotations (COCO)
        </Button>
      </ButtonGroup>

      {showLoading ? (
        <Box alignContent={"center"} width={"100%"}>
          <CircularProgress />
        </Box>
      ) : (
        <Stack spacing={4}>
          <Paper>
            <Box margin={2}>
              <Table size={"small"}>
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Animal ID</TableCell>
                    <TableCell>Species</TableCell>
                    <TableCell>Appearances</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Array.from(annotationsByName).map(
                    ([name, annotations], i) => (
                      <TableRow>
                        <TableCell>{i + 1}</TableCell>
                        <TableCell>{name}</TableCell>
                        <TableCell>Leopard</TableCell>
                        <TableCell>{annotations.length}</TableCell>
                      </TableRow>
                    )
                  )}
                </TableBody>
              </Table>
            </Box>
          </Paper>
          {Array.from(annotationsByName).map(([name, annotations]) => (
            <AnimalBreakdown name={name} annotations={annotations} key={name} />
          ))}
        </Stack>
      )}
    </Stack>
  );
}

function AnimalBreakdown(props: {
  name: string;
  annotations: Array<Annotation>;
}) {
  return (
    <Box>
      <Accordion defaultExpanded={true}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <h3>
            Animal ID: {props.name} ({props.annotations.length} images)
          </h3>
        </AccordionSummary>
        <AccordionDetails>
          <ImageList cols={4} gap={12}>
            {props.annotations.map((annotation) => (
              <ImageListItem key={annotation.image_src}>
                <img
                  src={annotation.annotated_image_src}
                  srcSet={annotation.annotated_image_src}
                  alt={annotation.annotated_image_src}
                  loading="lazy"
                />
                <ImageListItemBar
                  position={"top"}
                  subtitle={`Confidence: ${
                    Math.floor(Math.random() * 50 + 950) / 10.0
                  }%`}
                />
                <ButtonGroup variant={"text"} fullWidth>
                  <Button size={"small"} href={"#"}>
                    <Download /> Annotations
                  </Button>
                  <Button size={"small"} href={"#"}>
                    <Upload /> Corrections
                  </Button>
                </ButtonGroup>
              </ImageListItem>
            ))}
          </ImageList>
        </AccordionDetails>
      </Accordion>
    </Box>
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

interface PredictionRequest {}

interface PredictionResponse {
  annotations: Array<Annotation>;
}

interface Annotation {
  image_src: string;
  annotated_image_src: string;
  name: string;
}

export function fetchPredictions(
  req: PredictionRequest
): Promise<PredictionResponse> {
  return fetch("/api/v1/predict", {
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
