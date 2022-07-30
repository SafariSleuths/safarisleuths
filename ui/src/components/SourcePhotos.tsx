import React, { useEffect, useState } from "react";
import { Stack } from "@mui/material";
import { SessionSelect } from "./SessionSelect";
import { listImages } from "../actions/Images";
import { UploadImageForm } from "./UploadImageForm";
import { UploadedImagesDisplay } from "./UploadedImagesDisplay";

export function SourcePhotos(props: {
  sessionID: string;
  setSessionID: (v: string) => void;
}) {
  const [uploadedImages, setUploadedImages] = useState<
    Array<string> | undefined
  >(undefined);

  useEffect(() => {
    if (uploadedImages === undefined) {
      listImages(props.sessionID).then((data) =>
        setUploadedImages(data.images)
      );
    }
  });

  return (
    <Stack spacing={2}>
      <p>Upload new photos to use for predictions.</p>
      <SessionSelect
        sessionID={props.sessionID}
        setSessionID={props.setSessionID}
        setUploadedFiles={setUploadedImages}
      />
      <UploadImageForm
        sessionID={props.sessionID}
        uploadedImages={uploadedImages}
        setUploadedImages={setUploadedImages}
      />
      <UploadedImagesDisplay
        sessionID={props.sessionID}
        uploadedImages={uploadedImages || []}
        setUploadedImages={setUploadedImages}
      />
    </Stack>
  );
}
