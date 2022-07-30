import { Annotation, Undetected } from "../actions/Annotations";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import React from "react";

export function SummaryTable(props: {
  annotationsByName: Map<string, Array<Annotation>>;
}) {
  return (
    <Table size={"small"}>
      <TableHead>
        <TableRow>
          <TableCell>#</TableCell>
          <TableCell>Animal ID</TableCell>
          <TableCell>Species</TableCell>
          <TableCell>Appearances</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {Array.from(props.annotationsByName)
          .filter(([name, _]) => name !== Undetected)
          .map(([name, annotations], i) => (
            <TableRow key={i}>
              <TableCell>{i + 1}</TableCell>
              <TableCell>{name}</TableCell>
              <TableCell>
                {annotations[0].predicted_species.replace("_", " ")}
              </TableCell>
              <TableCell>{annotations.length}</TableCell>
            </TableRow>
          ))}
      </TableBody>
    </Table>
  );
}
