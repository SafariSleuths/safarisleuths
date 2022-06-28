import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Modal,
  Paper,
  Stack,
  SxProps,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Theme,
  Typography,
} from "@mui/material";

import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";

import { Download, ExpandMore, Upload } from "@mui/icons-material";

const MinConfidence = 0.89;

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

  const lowConfidenceAnnotations = (
    predictionResponse?.annotations || []
  ).filter((a) => a.confidence < MinConfidence);

  const annotationsByName = (predictionResponse?.annotations || [])
    .filter((a) => a.confidence >= MinConfidence)
    .reduce(
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
          <LowConfidence annotations={lowConfidenceAnnotations} />
          {Array.from(annotationsByName).map(([name, annotations]) => (
            <AnimalBreakdown name={name} annotations={annotations} key={name} />
          ))}
        </Stack>
      )}
    </Stack>
  );
}

function LowConfidence(props: { annotations: Array<Annotation> }) {
  return (
    <Box>
      <Accordion defaultExpanded={true}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <h3>Low Confidence ({props.annotations.length} images)</h3>
        </AccordionSummary>
        <AccordionDetails>
          <AnimalImageList annotations={props.annotations} />
        </AccordionDetails>
      </Accordion>
    </Box>
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
          <AnimalImageList annotations={props.annotations} />
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}

function AnimalImageList(props: { annotations: Array<Annotation> }) {
  return (
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
            subtitle={`Confidence: ${annotation.confidence * 100}%`}
          />
          <AnnotationButtonsAndModal annotation={annotation} />
        </ImageListItem>
      ))}
    </ImageList>
  );
}

function AnnotationButtonsAndModal(props: { annotation: Annotation }) {
  const data = JSON.stringify(props.annotation, null, 2);
  const [showAnnotations, setShowAnnotations] = React.useState(false);
  const [showForm, setShowForm] = React.useState(false);
  const [formError, setFormError] = React.useState<null | string>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  const boxStyle = {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    bgcolor: "background.paper",
    border: "2px solid #000",
    boxShadow: 24,
    p: 4,
  };

  return (
    <>
      <ButtonGroup variant={"text"} fullWidth>
        <Button size={"small"} onClick={() => setShowAnnotations(true)}>
          <Download /> Annotations
        </Button>
        <Button size={"small"} onClick={() => setShowForm(true)}>
          <Upload /> Corrections
        </Button>
      </ButtonGroup>
      <Modal open={showAnnotations} onClose={() => setShowAnnotations(false)}>
        <Box sx={boxStyle} textOverflow={"scroll"} minWidth={750}>
          <pre style={{ maxHeight: "500px", overflow: "scroll" }}>{data}</pre>
        </Box>
      </Modal>
      <Modal open={showForm} onClose={() => setShowForm(false)}>
        <Box sx={boxStyle} overflow={"scroll"} width={750}>
          <TextField
            ref={inputRef}
            fullWidth
            label={"COCO Annotation"}
            multiline
            rows={25}
            onChange={(e) => {
              try {
                JSON.parse(e.target.value);
              } catch (err) {
                setFormError(`${err}`);
                return;
              }
              setFormError(null);
            }}
          />
          <Button
            fullWidth
            variant={"contained"}
            color={"primary"}
            disabled={formError !== null}
            onClick={() => {
              setShowForm(false);
            }}
          >
            Submit
          </Button>
          <Box hidden={formError === null} paddingTop={2}>
            <Typography style={{ color: "warning" }}>{formError}</Typography>
          </Box>
        </Box>
      </Modal>
    </>
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
  confidence: number;
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
