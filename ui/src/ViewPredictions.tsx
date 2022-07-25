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
import {
  Annotation,
  fetchPredictions,
  readAnnotationsCache,
  writeAnnotationsCache,
} from "./Predictions";

export function ViewPredictions(props: { sessionID: string }) {
  const [annotations, setAnnotations] = useState<Array<Annotation> | undefined>(
    readAnnotationsCache()
  );

  const [showLoading, setShowLoading] = useState(false);

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
    writeAnnotationsCache(newAnnotations);
    setAnnotations(newAnnotations);
  };

  return (
    <Stack spacing={2}>
      <p>
        Compute predictions and review results. Once images have been reviewed,
        they can be used to fine-tuning the model for future predictions. The
        demo uses training images and random a confidence score for the
        predictions. All the results have been precomputed, so the "Compute
        Results" button will work very quickly; once we have all the models in
        place, this will take significantly longer to complete. We haven't wired
        in the retraining pipeline, so the retraining button is disabled.
      </p>
      <TopButtonGroup
        sessionID={props.sessionID}
        setAnnotations={setAnnotations}
        setShowLoading={setShowLoading}
        jsonDownloadUrl={jsonDownloadUrl}
      />
      <DisplayAnnotations
        sessionID={props.sessionID}
        showLoading={showLoading}
        updateAnnotations={updateAnnotations}
        annotationsByName={annotationsByName}
      />
    </Stack>
  );
}

function TopButtonGroup(props: {
  sessionID: string;
  setShowLoading: (v: boolean) => void;
  setAnnotations: (v: Array<Annotation>) => void;
  jsonDownloadUrl: string | undefined;
}) {
  const getPredictions = () =>
    fetchAndSortPredictions(
      props.sessionID,
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
  sessionID: string,
  setShowLoading: (v: boolean) => void,
  setAnnotations: (v: Array<Annotation>) => void
) {
  setShowLoading(true);
  fetchPredictions(sessionID).then((data) => {
    data.annotations.sort((a, b) => {
      switch (true) {
        case a.predicted_name == b.predicted_name:
          return 0;
        case a.predicted_name !== undefined && b.predicted_name !== undefined:
          return a.predicted_name?.localeCompare(b.predicted_name || "") || 0;
        case a.predicted_name == undefined:
          return 1;
        default:
          return -1;
      }
    });
    writeAnnotationsCache(data.annotations);
    setAnnotations(data.annotations);
    setShowLoading(false);
  });
}

function DisplayAnnotations(props: {
  sessionID: string;
  showLoading: boolean;
  updateAnnotations: (updates: Array<Annotation>) => void;
  annotationsByName: Map<string, Array<Annotation>>;
}) {
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
        sessionID={props.sessionID}
        name={Undetected}
        subtitle={"We could not detect or label the animal in these images."}
        annotations={props.annotationsByName.get(Undetected) || []}
        setAnnotations={props.updateAnnotations}
      />
      {Array.from(props.annotationsByName)
        .filter(([name, _]) => name !== Undetected)
        .map(([name, annotations]) => (
          <AnimalBreakdown
            sessionID={props.sessionID}
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
        {Array.from(props.annotationsByName)
          .filter(([name, _]) => name != Undetected)
          .map(([name, annotations], i) => (
            <TableRow key={i}>
              <TableCell>{i + 1}</TableCell>
              <TableCell>{name}</TableCell>
              <TableCell>
                {annotations[0].predicted_species.replace("_", " ")}
              </TableCell>
              <TableCell>{annotations.length}</TableCell>
            </TableRow>
          ))}
      </TableBody>
    </Table>
  );
}

const Undetected = "undetected";

function AnimalBreakdown(props: {
  sessionID: string;
  name: string;
  annotations: Array<Annotation>;
  setAnnotations: (v: Array<Annotation>) => void;
  subtitle: string;
}) {
  if (props.annotations.length == 0) {
    return <Box />;
  }

  const pendingReview = props.annotations.filter((a) => a.reviewed).length;
  let title = `Animal ID: ${props.name} (${pendingReview}/${props.annotations.length} reviewed)`;
  if (props.name == Undetected) {
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
            sessionID={props.sessionID}
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
  sessionID: string;
}) {
  props.annotations.sort((a, b) => {
    let a_score = 0;
    let b_score = 0;
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
      return a.predicted_name.localeCompare(b.predicted_name);
    }
    return a_score - b_score;
  });

  return (
    <ImageList cols={3} gap={12}>
      {props.annotations.map((annotation, i) => (
        <AnnotationImage
          sessionID={props.sessionID}
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
  sessionID: string;
  annotation: Annotation;
  setAnnotation: (v: Annotation) => void;
}) {
  const src =
    props.annotation.annotated_file_name || props.annotation.file_name;
  const alt = `${props.annotation.file_name.slice(
    props.annotation.file_name.lastIndexOf("/")
  )} with bounding box`;
  const [openImageModal, setOpenImageModal] = useState(false);

  let subtitle = `Pending Review`;
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
      <ImageListItemBar
        position={"top"}
        subtitle={
          <Grid container flexDirection={"row"}>
            <Grid item xs={6}>
              <Tooltip title={"Individual Classifier Confidence"}>
                <span>{subtitle}</span>
              </Tooltip>
            </Grid>
            <Grid item style={{ textAlign: "right" }} xs={6}>
              <Tooltip title={"Lat: 0.000, Long: 0.000"}>
                <span>Location: Safari</span>
              </Tooltip>
            </Grid>
          </Grid>
        }
      />
      <AnnotationButtonsAndModal
        sessionID={props.sessionID}
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
  sessionID: string;
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
        SessionID: props.sessionID,
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

  let content = (
    <>
      <ContentCopy /> Annotation
    </>
  );

  if (copied) {
    content = (
      <>
        <Check /> Copied!
      </>
    );
  }

  return (
    <Tooltip title="Copy the annotation to the clipboard." arrow>
      <Button size={"small"} onClick={onButtonClick}>
        {content}
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
