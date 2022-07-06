import React, { ChangeEvent, useEffect, useState } from "react";
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";

import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";

import {
  Download,
  ExpandMore,
  ContentCopy,
  Edit,
  Check,
  Cancel,
} from "@mui/icons-material";

const MinConfidence = 0.89;

interface PredictionRequest {}

interface PredictionResponse {
  annotations: Array<Annotation>;
}

interface Prediction {
  name: string;
  confidence: number;
}

interface Annotation {
  id: number;
  image_id: number;
  bbox: Array<number>;
  name: string;
  species: string;
  confidence: number;
  predictions: Array<Prediction>;
  image_src: string;
  annotated_image_src: string;
  reviewed: boolean | undefined;
  ignored: boolean | undefined;
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

const AnnotationsCacheKey = "prediction";

function readAnnotationsCache(): Array<Annotation> | undefined {
  const localAnnotations = localStorage.getItem(AnnotationsCacheKey);
  if (localAnnotations !== null) {
    return JSON.parse(localAnnotations);
  }
  return undefined;
}

function writeAnnotationsCache(annotations: Array<Annotation>) {
  localStorage.setItem(AnnotationsCacheKey, JSON.stringify(annotations));
}

export function Predictions(props: { sessionID: string }) {
  const [annotations, setAnnotations] = useState<Array<Annotation> | undefined>(
    readAnnotationsCache()
  );

  const [showLoading, setShowLoading] = useState(false);

  function getPredictions() {
    setShowLoading(true);
    fetchPredictions({ session_id: props.sessionID }).then((data) => {
      writeAnnotationsCache(data.annotations);
      setAnnotations(data.annotations);
      setShowLoading(false);
    });
  }

  const jsonDownloadUrl = useJsonDownloadUrl(annotations);

  const lowConfidenceAnnotations = (
    annotations || ([] as Array<Annotation>)
  ).filter((a) => a.confidence < MinConfidence);

  const annotationsByName: Map<string, Array<Annotation>> = (
    annotations || ([] as Array<Annotation>)
  ).reduce(
    (a, b) => a.set(b.name, [...(a.get(b.name) || []), b]),
    new Map<string, Array<Annotation>>()
  );

  const updateAnnotations = (updates: Array<Annotation>) => {
    const annotationsById: Map<number, Annotation> = (
      annotations || ([] as Array<Annotation>)
    ).reduce((a, b) => a.set(b.id, b), new Map<number, Annotation>());
    updates.forEach((annotation) =>
      annotationsById.set(annotation.id, annotation)
    );
    setAnnotations(Array.from(annotationsById.values()));
  };

  return (
    <Stack spacing={2}>
      <p>
        Compute predictions and review results. Once images have been reviewed,
        they can be used to fine-tuning the model for future predictions.
      </p>
      <ButtonGroup>
        <Button onClick={getPredictions}>Compute Results</Button>
        <Button
          href={jsonDownloadUrl || "#"}
          disabled={jsonDownloadUrl === undefined}
          download={"results.json"}
        >
          <Download /> Annotations (COCO)
        </Button>
        <Button disabled>Start Retraining</Button>
      </ButtonGroup>

      {showLoading ? (
        <Box alignContent={"center"} width={"100%"}>
          <CircularProgress />
        </Box>
      ) : (
        <Stack spacing={4}>
          <Paper>
            <Box margin={2}>
              <h3>Summary</h3>
              <SummaryTable annotationsByName={annotationsByName} />
            </Box>
          </Paper>
          {Array.from(annotationsByName).map(([name, annotations]) => (
            <AnimalBreakdown
              key={name}
              name={name}
              annotations={annotations}
              setAnnotations={updateAnnotations}
            />
          ))}
        </Stack>
      )}
    </Stack>
  );
}

function SummaryTable(props: {
  annotationsByName: Map<string, Array<Annotation>>;
}) {
  return (
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
        {Array.from(props.annotationsByName).map(([name, annotations], i) => (
          <TableRow key={i}>
            <TableCell>{i + 1}</TableCell>
            <TableCell>{name}</TableCell>
            <TableCell>{annotations[0].species}</TableCell>
            <TableCell>{annotations.length}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function AnimalBreakdown(props: {
  name: string;
  annotations: Array<Annotation>;
  setAnnotations: (v: Array<Annotation>) => void;
}) {
  const pendingReview = props.annotations.filter((a) => a.reviewed).length;
  return (
    <Box>
      <Accordion defaultExpanded={true}>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <h3>
            Animal ID: {props.name} ({pendingReview}/{props.annotations.length}{" "}
            reviewed)
          </h3>
        </AccordionSummary>
        <AccordionDetails>
          <AnimalImageList
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
}) {
  props.annotations.sort((a, b) => {
    let a_score = a.confidence;
    let b_score = b.confidence;
    if (a.reviewed) {
      a_score = 100;
    }
    if (b.reviewed) {
      b_score = 100;
    }
    if (a.ignored) {
      a_score = 200;
    }
    if (b.ignored) {
      b_score = 200;
    }
    if (a_score == b_score) {
      return a.name.localeCompare(b.name);
    }
    return a_score - b_score;
  });

  return (
    <ImageList cols={3} gap={12}>
      {props.annotations.map((annotation, i) => (
        <AnnotationImage
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

function AnnotationImage(props: {
  annotation: Annotation;
  setAnnotation: (v: Annotation) => void;
}) {
  const src = props.annotation.annotated_image_src;
  const alt = `${props.annotation.image_src.slice(
    props.annotation.image_src.lastIndexOf("/")
  )} with bounding box`;
  const [openImageModal, setOpenImageModal] = React.useState(false);

  let subtitle = `Confidence: ${(props.annotation.confidence * 100).toFixed(
    2
  )}%`;

  if (props.annotation.reviewed) {
    subtitle = "✔ Reviewed";
  }

  if (props.annotation.ignored) {
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
      <ButtonGroup fullWidth variant={"text"}>
        <Tooltip
          title="Accept the predicted annotation as is and use it for retraining."
          arrow
        >
          <Button
            size={"small"}
            onClick={() => {
              updatedAnnotation.reviewed = true;
              updatedAnnotation.ignored = false;
              submitAnnotation();
            }}
          >
            <Check /> Accept
          </Button>
        </Tooltip>
        <Tooltip
          title="Ignore this prediction and do not use the annotation for retraining."
          arrow
        >
          <Button
            size={"small"}
            onClick={() => {
              updatedAnnotation.ignored = true;
              submitAnnotation();
            }}
          >
            <Cancel /> Ignore
          </Button>
        </Tooltip>
        <Tooltip
          title="Make corrections to annotation. After corrections are made, this image and annotation will be used for retraining."
          arrow
        >
          <Button size={"small"} onClick={() => setShowForm(true)}>
            <Edit /> Corrections
          </Button>
        </Tooltip>

        <CopyButton annotationJSON={annotationJSON} />
      </ButtonGroup>
      <Modal open={showForm} onClose={() => setShowForm(false)}>
        <Box sx={boxStyle} overflow={"scroll"} width={750}>
          <TextField
            ref={inputRef}
            fullWidth
            label={"Annotation JSON"}
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
              updatedAnnotation.ignored = false;
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
    <Tooltip title="Copy the annotation to the clipboard." arrow>
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
    </Tooltip>
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
