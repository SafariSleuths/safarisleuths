import React, { useState } from "react";
import { Box, ImageListItem, ImageListItemBar } from "@mui/material";
import { ImageModal } from "./ImageModal";

export function RetrainingImageItem(props: {
  cropped_file_name: string;
  predicted_name: string;
  predicted_species: string;
}) {
  const [openImageModal, setOpenImageModal] = useState(false);
  const title = (
    <Box>
      Name: {props.predicted_name}
      <br />
      Species: {props.predicted_species}
    </Box>
  );
  return (
    <ImageListItem>
      <img
        style={{ height: 300, width: 300 }}
        src={props.cropped_file_name}
        srcSet={props.cropped_file_name}
        alt={props.cropped_file_name}
        loading="lazy"
        onClick={() => setOpenImageModal(true)}
      />
      <ImageModal
        src={props.cropped_file_name}
        alt={props.cropped_file_name}
        open={openImageModal}
        setOpen={setOpenImageModal}
      />
      <ImageListItemBar position={"below"} subtitle={title} />
    </ImageListItem>
  );
}
