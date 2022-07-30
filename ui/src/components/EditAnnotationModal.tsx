import { Box, Button, Modal, TextField, Typography } from "@mui/material";
import React, { ChangeEvent } from "react";
import { Annotation } from "../actions/Annotations";

export function EditAnnotationModal(props: {
  annotation: Annotation;
  showForm: boolean;
  setShowForm: (v: boolean) => void;
  submit: (annotation: Annotation) => void;
}) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [formError, setFormError] = React.useState<null | string>(null);

  let newAnnotation: Annotation = { ...props.annotation };

  const onTextFieldChange = (
    e: ChangeEvent<HTMLTextAreaElement | HTMLInputElement>
  ) => {
    try {
      newAnnotation = JSON.parse(e.target.value);
      setFormError(null);
    } catch (err) {
      setFormError(`${err}`);
    }
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
    <Modal open={props.showForm} onClose={() => props.setShowForm(false)}>
      <Box sx={boxStyle} overflow={"scroll"} width={750}>
        <TextField
          ref={inputRef}
          fullWidth
          label={"Annotation JSON"}
          multiline
          rows={25}
          defaultValue={JSON.stringify(props.annotation, null, 2)}
          onChange={onTextFieldChange}
        />
        <Button
          fullWidth
          variant={"contained"}
          color={"primary"}
          disabled={formError !== null}
          onClick={() => {
            newAnnotation.accepted = true;
            newAnnotation.ignored = false;
            props.submit(newAnnotation);
            props.setShowForm(false);
          }}
        >
          Submit
        </Button>
        <Box hidden={formError === null} paddingTop={2}>
          <Typography style={{ color: "warning" }}>{formError}</Typography>
        </Box>
      </Box>
    </Modal>
  );
}
