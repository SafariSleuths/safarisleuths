import React, { useRef, useState } from "react";
import { Box, Button, CircularProgress, FormControl } from "@mui/material";
import { uploadImages } from "../actions/Images";

export function UploadImageForm(props: {
  collectionID: string;
  uploadedImages: Array<string> | undefined;
  setUploadedImages: (value: Array<string> | undefined) => void;
}) {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showLoading, setShowLoading] = useState(false);

  return (
    <Box marginTop={2}>
      <FormControl>
        <input
          ref={inputRef}
          multiple={true}
          accept={"image/jpeg,image/png"}
          type={"file"}
          onChange={(e) => setSelectedFiles(e.target.files)}
        />
        <Button
          disabled={selectedFiles == null}
          onClick={() => {
            setShowLoading(true);
            uploadImages(props.collectionID, selectedFiles).then((uploaded) => {
              setShowLoading(false);
              setSelectedFiles(null);
              props.setUploadedImages([
                ...uploaded,
                ...(props.uploadedImages ?? []),
              ]);
            });
            if (inputRef.current != null) {
              inputRef.current.value = "";
            }
          }}
        >
          Upload Photos
        </Button>
      </FormControl>
      <Box hidden={!showLoading}>
        <CircularProgress />{" "}
      </Box>
    </Box>
  );
}
