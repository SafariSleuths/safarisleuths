import {
  Button,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Stack,
} from "@mui/material";
import { deleteImages } from "../actions/Images";
import React, { useState } from "react";
import { ImageModal } from "./ImageModal";

export function UploadedImagesDisplay(props: {
  collectionID: string;
  uploadedImages: Array<string>;
  setUploadedImages: (v: Array<string>) => void;
}) {
  return (
    <Stack alignItems={"center"}>
      <ImageList cols={4} gap={12}>
        {props.uploadedImages.map((src, i) => (
          <UploadedImageItem
            key={i}
            src={src}
            collectionID={props.collectionID}
            uploadedImages={props.uploadedImages}
            setUploadedImages={props.setUploadedImages}
          />
        ))}
      </ImageList>
    </Stack>
  );
}

function UploadedImageItem(props: {
  src: string;
  collectionID: string;
  uploadedImages: Array<string>;
  setUploadedImages: (v: Array<string>) => void;
}) {
  const [openImageModal, setOpenImageModal] = useState(false);
  const title = `File name: ${props.src.split("/").reverse()[0]}`;

  const onClickDelete = () =>
    deleteImages(props.collectionID, [props.src]).then(() =>
      props.setUploadedImages(
        props.uploadedImages.filter((n) => n != props.src)
      )
    );

  return (
    <ImageListItem>
      <img
        style={{ height: 350, width: 350 }}
        src={props.src}
        srcSet={props.src}
        alt={title}
        loading="lazy"
        onClick={() => setOpenImageModal(true)}
      />
      <ImageModal
        src={props.src}
        alt={title}
        open={openImageModal}
        setOpen={setOpenImageModal}
      />
      <ImageListItemBar position={"below"} subtitle={title} />
      <Button fullWidth onClick={onClickDelete}>
        Delete
      </Button>
    </ImageListItem>
  );
}
