import { RetrainEventLog } from "../actions/RetrainingLogs";
import {
  Box,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
import React from "react";

export function RetrainingLogsTable(props: { logs: Array<RetrainEventLog> }) {
  let content = (
    <Table size={"small"}>
      <TableBody>
        {props.logs.map((log, i) => (
          <TableRow key={i}>
            <TableCell align="left">
              {new Date(log.created_at * 1000).toLocaleString()}
            </TableCell>
            <TableCell align="left">{log.message}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );

  if (props.logs.length === 0) {
    content = (
      <Box>
        <pre>Nothing here 🤷</pre>
      </Box>
    );
  }
  return (
    <Stack>
      <h3>Retraining Logs:</h3>
      {content}
    </Stack>
  );
}
