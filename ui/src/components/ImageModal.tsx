import { Box, Modal } from "@mui/material";
import React from "react";

export function ImageModal(props: {
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
          src={props.src}
          srcSet={props.src}
          alt={props.alt}
          loading="lazy"
        />
      </Box>
    </Modal>
  );
}
