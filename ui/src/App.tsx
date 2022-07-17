import React from "react";
import "./App.css";
import { Box, Stack, Tab, Tabs } from "@mui/material";
import { Predictions } from "./Predictions";
import { SourceFiles } from "./SourceFiles";
import { KnownIndividuals } from "./KnownIndividuals";
import { Documentation } from "./Documentation";

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

function MainMenu() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const [sessionID, setSessionID] = React.useState("demo");
  let content = <Box />;
  switch (value) {
    case 0:
      content = (
        <SourceFiles sessionID={sessionID} setSessionID={setSessionID} />
      );
      break;
    case 1:
      content = <Predictions sessionID={"0"} />;
      break;
    case 2:
      content = <KnownIndividuals />;
      break;
    case 3:
      content = <Documentation />;
      break;
  }

  return (
    <Box sx={{ width: "100%" }}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={value}
          onChange={handleChange}
          aria-label="basic tabs example"
        >
          <Tab label="Source Photos" />
          <Tab label="Prediction Results" />
          <Tab label="Known Individuals" />
          <Tab label="Documentation" />
        </Tabs>
      </Box>
      {content}
    </Box>
  );
}
