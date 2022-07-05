import React from "react";
import "./App.css";
import { Box, Grid } from "@mui/material";
import { Predictions } from "./Predictions";
import { UploadMenu } from "./UploadMenu";

export default function App() {
  return (
    <Box paddingX={6} paddingBottom={4}>
      <h1>Safari Sleuths</h1>
      <h2>Individual Animal Identifier</h2>
      <Grid container spacing={2}>
        <Grid item width={350}>
          <UploadMenu sessionID={"0"} />
        </Grid>
        <Grid item xs={9}>
          <Predictions sessionID={"0"} />
        </Grid>
      </Grid>
    </Box>
  );
}
