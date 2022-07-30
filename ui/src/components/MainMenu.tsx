import React from "react";
import { Box, Tab, Tabs } from "@mui/material";
import { SourcePhotos } from "./SourcePhotos";
import { PredictionResults } from "./PredictionResults";
import { KnownIndividuals } from "./KnownIndividuals";
import { Documentation } from "./Documentation";
import { Retraining } from "./Retraining";

export function MainMenu() {
  const [value, setValue] = React.useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const [sessionID, setSessionID] = React.useState("Demo");
  let content = <Box />;
  switch (value) {
    case 0:
      content = (
        <SourcePhotos sessionID={sessionID} setSessionID={setSessionID} />
      );
      break;
    case 1:
      content = <PredictionResults sessionID={sessionID} />;
      break;
    case 2:
      content = <Retraining sessionID={sessionID} />;
      break;
    case 3:
      content = <KnownIndividuals />;
      break;
    case 4:
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
          <Tab label="Retraining" />
          <Tab label="Known Individuals" />
          <Tab label="Documentation" />
        </Tabs>
      </Box>
      {content}
    </Box>
  );
}
