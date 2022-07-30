import React from "react";
import "./App.css";
import { Box, Stack } from "@mui/material";
import { MainMenu } from "./components/MainMenu";

export default function App() {
  return (
    <Box paddingX={6} paddingBottom={4}>
      <Stack spacing={2}>
        <h1>
          Safari Sleuths | <small>Individual Animal Identifier</small>
        </h1>
        <MainMenu />
      </Stack>
    </Box>
  );
}
