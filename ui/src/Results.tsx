import React, { ChangeEvent, useEffect, useState } from "react";
import {
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  Grid,
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

import {
  Download,
  ExpandMore,
  Upload,
  ContentCopy,
  CopyAll,
  Edit,
  Check,
  Cancel,
} from "@mui/icons-material";

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
  const reviewed = false;

  return (
    <Box>
      <Accordion defaultExpanded={true}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <h3>
            Low Confidence ({props.annotations.length} images)
            {reviewed ? (
              <Typography color={"success"}>Reviewed</Typography>
            ) : (
              <Typography color={"success"}>Needs Review</Typography>
            )}
          </h3>
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
  const [annotations, setAnnotations] = React.useState(props.annotations);
  return (
    <ImageList cols={4} gap={12}>
      {annotations.map((annotation, i) => (
        <AnnotationImage
          key={i}
          annotation={annotation}
          setAnnotation={(v: Annotation) => {
            const newAnnotations = [...annotations];
            newAnnotations[i] = v;
            setAnnotations(newAnnotations);
          }}
        />
      ))}
    </ImageList>
  );
}

function AnnotationImage(props: {
  annotation: Annotation;
  setAnnotation: (v: Annotation) => void;
}) {
  const src = props.annotation.annotated_image_src;
  const alt = `${props.annotation.image_src.slice(
    props.annotation.image_src.lastIndexOf("/")
  )} with bounding box`;
  const [openImageModal, setOpenImageModal] = React.useState(false);

  let subtitle = `Confidence: ${props.annotation.confidence * 100}%`;

  if (props.annotation.reviewed) {
    subtitle = "✔ Reviewed";
  }

  if (props.annotation.ignore) {
    subtitle = "❌ Ignored";
  }

  return (
    <ImageListItem>
      <img
        src={src}
        srcSet={src}
        alt={alt}
        loading="lazy"
        onClick={() => setOpenImageModal(true)}
      />
      <ImageModal
        src={src}
        alt={alt}
        open={openImageModal}
        setOpen={setOpenImageModal}
      />
      <ImageListItemBar position={"top"} subtitle={subtitle} />
      <AnnotationButtonsAndModal
        annotation={props.annotation}
        setAnnotation={props.setAnnotation}
      />
    </ImageListItem>
  );
}

function ImageModal(props: {
  src: string;
  alt: string;
  open: boolean;
  setOpen: (v: boolean) => void;
}) {
  return (
    <Modal open={props.open} onClose={() => props.setOpen(false)}>
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="100vh"
      >
        <img
          width={"75%"}
          height={"auto"}
          src={props.src}
          srcSet={props.src}
          alt={props.alt}
          loading="lazy"
        />
      </Box>
    </Modal>
  );
}

function AnnotationButtonsAndModal(props: {
  annotation: Annotation;
  setAnnotation: (v: Annotation) => void;
}) {
  const annotationJSON = JSON.stringify(props.annotation, null, 2);
  const [showForm, setShowForm] = React.useState(false);
  const [formError, setFormError] = React.useState<null | string>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);
  let updatedAnnotation = props.annotation;

  const onTextFieldChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    try {
      updatedAnnotation = JSON.parse(e.target.value);
      setFormError(null);
    } catch (err) {
      setFormError(`${err}`);
    }
  };

  const submitAnnotation = () => {
    const annotationsJSON = JSON.stringify([updatedAnnotation]);
    fetch("/api/v1/annotations", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: annotationsJSON,
    })
      .then(() => {
        setShowForm(false);
        props.setAnnotation(updatedAnnotation);
      })
      .catch((reason) => setFormError(reason));
  };

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
        <Button size={"small"} onClick={() => setShowForm(true)}>
          <Edit /> Corrections
        </Button>
        <Button
          size={"small"}
          onClick={() => {
            updatedAnnotation.ignore = true;
            submitAnnotation();
          }}
        >
          <Cancel /> Ignore
        </Button>
      </ButtonGroup>
      <Modal open={showForm} onClose={() => setShowForm(false)}>
        <Box sx={boxStyle} overflow={"scroll"} width={750}>
          <TextField
            ref={inputRef}
            fullWidth
            label={"COCO JSON"}
            multiline
            rows={25}
            defaultValue={annotationJSON}
            onChange={onTextFieldChange}
          />
          <Button
            fullWidth
            variant={"contained"}
            color={"primary"}
            disabled={formError !== null}
            onClick={() => {
              updatedAnnotation.reviewed = true;
              updatedAnnotation.ignore = false;
              submitAnnotation();
            }}
          >
            Submit
          </Button>
          <Box hidden={formError === null} paddingTop={2}>
            <Typography style={{ color: "warning" }}>{formError}</Typography>
          </Box>
        </Box>
      </Modal>
      <CopyButton annotationJSON={annotationJSON} />
    </>
  );
}

function CopyButton(props: { annotationJSON: string }) {
  const [copied, setCopied] = React.useState(false);
  const onButtonClick = () =>
    navigator.clipboard
      .writeText(props.annotationJSON)
      .then(() => {
        setCopied(true);
        return new Promise((resolve) => setTimeout(resolve, 1000));
      })
      .then(() => setCopied(false));

  return (
    <Button size={"small"} onClick={onButtonClick}>
      {copied ? (
        <>
          <Check /> Copied!
        </>
      ) : (
        <>
          <ContentCopy /> Annotation
        </>
      )}
    </Button>
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
  reviewed: boolean | undefined;
  ignore: boolean | undefined;
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
