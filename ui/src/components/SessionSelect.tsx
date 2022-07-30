import React, { useEffect, useState } from "react";
import {
  Button,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import { getSessions, putSession, Session } from "../actions/Sessions";

export function SessionSelect(props: {
  sessionID: string;
  setSessionID: (v: string) => void;
  setUploadedFiles: (v: Array<string> | undefined) => void;
}) {
  const [sessions, setSessions] = useState<Array<Session> | undefined>(
    undefined
  );

  useEffect(() => {
    if (sessions === undefined) {
      getSessions().then((sessions) => setSessions(sessions));
    }
  });

  const [newSession, setNewSession] = React.useState("");
  const [canSubmit, setCanSubmit] = React.useState(false);

  return (
    <Grid marginTop={2} container>
      <Grid item xs={3}>
        <h4>Choose an existing session:</h4>
        <InputLabel id="session">Sessions</InputLabel>
        <Select
          size={"small"}
          value={sessions !== undefined ? props.sessionID : ""}
          label="Sessions"
          id="session"
          onChange={(e) => props.setSessionID(e.target.value)}
        >
          {sessions?.map((session) => (
            <MenuItem key={session.id} value={session.id}>
              {session.name}
            </MenuItem>
          ))}
        </Select>
      </Grid>
      <Grid item xs={9}>
        <h4>Create a new session:</h4>
        <Grid container spacing={1}>
          <Grid item>
            <TextField
              label={"Name"}
              size={"small"}
              onChange={(e) => {
                setNewSession(e.target.value);
                props.setUploadedFiles(undefined);
                if (e.target.value !== "") {
                  setCanSubmit(true);
                }
              }}
            />
          </Grid>
          <Grid item>
            <Button
              variant={"outlined"}
              disabled={!canSubmit}
              onClick={() => {
                putSession(newSession).then((session) => {
                  setSessions([...(sessions || []), session]);
                  props.setSessionID(session.id);
                });
              }}
            >
              Submit
            </Button>
          </Grid>
        </Grid>
      </Grid>
    </Grid>
  );
}
