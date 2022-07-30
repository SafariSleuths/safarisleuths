import React from "react";
import { fetchAnnotations, Annotation } from "../actions/Annotations";
import { Box, ImageList } from "@mui/material";
import { RetrainingImageItem } from "./RetrainingImageItem";

export function RetrainImagesDisplay(props: { collectionID: string }) {
  const [annotations, setAnnotations] = React.useState<
    Array<Annotation> | undefined
  >(undefined);

  const loaded = React.useRef(false);
  React.useEffect(() => {
    if (!loaded.current) {
      fetchAnnotations(props.collectionID).then((newAnnotations) =>
        setAnnotations(newAnnotations.filter((a) => a.accepted))
      );
      loaded.current = true;
    }
  });

  if (annotations == undefined) {
    return (
      <Box>
        No images can be used for retraining. Please review images in the
        predictions tab.
      </Box>
    );
  }

  return (
    <Box>
      <h3>Images included in retraining</h3>
      <ImageList cols={5} gap={6}>
        {annotations
          .map((annotation) => ({
            file_name: annotation.cropped_file_name || "",
            name: annotation.predicted_name || "",
            species: annotation.predicted_species || "",
          }))
          .filter((v) => v.file_name != "")
          .filter((v) => v.name != "")
          .filter((v) => v.species != "")
          .map((v, i) => (
            <RetrainingImageItem
              key={i}
              cropped_file_name={v.file_name}
              predicted_name={v.name}
              predicted_species={v.species.replace("_", " ")}
            />
          ))}
      </ImageList>
    </Box>
  );
}
