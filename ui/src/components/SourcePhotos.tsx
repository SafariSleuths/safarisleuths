import React, { useEffect, useState } from "react";
import { Stack } from "@mui/material";
import { CollectionSelect } from "./CollectionSelect";
import { listImages } from "../actions/Images";
import { UploadImageForm } from "./UploadImageForm";
import { UploadedImagesDisplay } from "./UploadedImagesDisplay";

export function SourcePhotos(props: {
  collectionID: string;
  setCollectionID: (v: string) => void;
}) {
  const [uploadedImages, setUploadedImages] = useState<
    Array<string> | undefined
  >(undefined);

  useEffect(() => {
    if (uploadedImages === undefined) {
      listImages(props.collectionID).then((images) =>
        setUploadedImages(images)
      );
    }
  });

  return (
    <Stack spacing={2}>
      <p>Upload new photos to use for predictions.</p>
      <CollectionSelect
        collectionID={props.collectionID}
        setCollectionID={props.setCollectionID}
        setUploadedFiles={setUploadedImages}
      />
      <UploadImageForm
        collectionID={props.collectionID}
        uploadedImages={uploadedImages}
        setUploadedImages={setUploadedImages}
      />
      <UploadedImagesDisplay
        collectionID={props.collectionID}
        uploadedImages={uploadedImages || []}
        setUploadedImages={setUploadedImages}
      />
    </Stack>
  );
}
