import { Annotation, submitAnnotations } from "../actions/Annotations";
import { Button, ButtonGroup, Tooltip } from "@mui/material";
import React from "react";
import { Cancel, Check, ContentCopy, Edit } from "@mui/icons-material";
import { EditAnnotationModal } from "./EditAnnotationModal";

export function AnnotatedImageButtons(props: {
  annotation: Annotation;
  setAnnotation: (v: Annotation) => void;
  collectionID: string;
}) {
  const submit = (annotation: Annotation) => {
    submitAnnotations(props.collectionID, [annotation]).then(() =>
      props.setAnnotation(annotation)
    );
  };

  return (
    <ButtonGroup fullWidth variant={"text"}>
      <AcceptAnnotationButton annotation={props.annotation} submit={submit} />
      <IgnoreAnnotationButton annotation={props.annotation} submit={submit} />
      <EditAnnotationButton annotation={props.annotation} submit={submit} />
      <CopyAnnotationButton annotation={props.annotation} />
    </ButtonGroup>
  );
}

function AcceptAnnotationButton(props: {
  annotation: Annotation;
  submit: (annotation: Annotation) => void;
}) {
  return (
    <Tooltip
      title="Accept the predicted annotation as is and use it for retraining."
      arrow
    >
      <Button
        size={"small"}
        onClick={() => {
          let newAnnotation: Annotation = { ...props.annotation };
          newAnnotation.accepted = true;
          newAnnotation.ignored = false;
          props.submit(newAnnotation);
        }}
      >
        <Check /> Accept
      </Button>
    </Tooltip>
  );
}

function IgnoreAnnotationButton(props: {
  annotation: Annotation;
  submit: (annotation: Annotation) => void;
}) {
  return (
    <Tooltip
      title="Ignore this prediction and do not use the annotation for retraining."
      arrow
    >
      <Button
        size={"small"}
        onClick={() => {
          let newAnnotation: Annotation = { ...props.annotation };
          newAnnotation.ignored = true;
          props.submit(newAnnotation);
        }}
      >
        <Cancel /> Ignore
      </Button>
    </Tooltip>
  );
}

export function EditAnnotationButton(props: {
  annotation: Annotation;
  submit: (annotation: Annotation) => void;
}) {
  const [showForm, setShowForm] = React.useState(false);
  return (
    <>
      <Tooltip
        title="Make corrections to annotation. After corrections are made, this image and annotation will be used for retraining."
        arrow
      >
        <Button size={"small"} onClick={() => setShowForm(true)}>
          <Edit /> Corrections
        </Button>
      </Tooltip>
      <EditAnnotationModal
        annotation={props.annotation}
        submit={props.submit}
        showForm={showForm}
        setShowForm={setShowForm}
      />
    </>
  );
}

function CopyAnnotationButton(props: { annotation: Annotation }) {
  const annotationJSON = JSON.stringify(props.annotation, null, 2);
  const [copied, setCopied] = React.useState(false);
  const onButtonClick = () =>
    navigator.clipboard
      .writeText(annotationJSON)
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
