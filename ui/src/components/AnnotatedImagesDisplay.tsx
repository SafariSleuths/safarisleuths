import { Annotation } from "../actions/Annotations";
import React, { useState } from "react";
import { Grid, ImageListItem, ImageListItemBar, Tooltip } from "@mui/material";
import { ImageModal } from "./ImageModal";
import { AnnotatedImageButtons } from "./AnnotatedImageButtons";

export function AnnotatedImagesDisplay(props: {
  collectionID: string;
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
  if (props.annotation.accepted) {
    subtitle = "✔ Reviewed";
  }

  if (props.annotation.ignored) {
    subtitle = "❌ Ignored";
  }

  return (
    <ImageListItem sx={{ alignItems: "center" }}>
      <img
        style={{ height: 500, width: 520 }}
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
      <AnnotatedImageButtons
        collectionID={props.collectionID}
        annotation={props.annotation}
        setAnnotation={props.setAnnotation}
      />
    </ImageListItem>
  );
}
