import React from "react";
import "./App.css";
import { Box, Grid } from "@mui/material";
import { Results } from "./Results";
import { UploadMenu } from "./UploadMenu";

export default function App() {
  return (
    <Box paddingX={6} paddingBottom={4}>
      <h1>Zebra Counter</h1>
      <Grid container spacing={2}>
        <Grid item xs={3}>
          <Box width={300}>
            <UploadMenu sessionID={"0"} />
          </Box>
        </Grid>
        <Grid item xs={9}>
          <Results sessionID={"0"} />
        </Grid>
      </Grid>
    </Box>
  );
}
