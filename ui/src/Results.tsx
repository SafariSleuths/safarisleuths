import React, { useEffect, useState } from "react";
import { ApiResponse, fetchPhotoMetrics, PhotoMetrics } from "./ApiRequest";
import {
  Button,
  ButtonGroup,
  CircularProgress,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";

export function Results(props: { sessionID: string }) {
  const [apiResponse, setApiResponse] = useState<ApiResponse | undefined>(
    undefined
  );

  const [showLoading, setShowLoading] = useState(false);

  function getPredictions() {
    setApiResponse(undefined);
    setShowLoading(true);
    fetchPhotoMetrics({ session_id: props.sessionID }).then((data) => {
      setApiResponse(data);
      setShowLoading(false);
    });
  }

  const jsonDownloadUrl = useJsonDownloadUrl(apiResponse?.photo_metrics);
  const csvDownloadUrl = useCSVDownloadUrl(apiResponse?.photo_metrics);

  return (
    <Stack spacing={2}>
      <h2>Results</h2>
      <ButtonGroup>
        <Button onClick={getPredictions}>Compute Results</Button>
        <Button
          href={jsonDownloadUrl || "#"}
          disabled={jsonDownloadUrl === undefined}
          download={"results.json"}
        >
          Download JSON
        </Button>
        <Button
          href={csvDownloadUrl || "#"}
          disabled={csvDownloadUrl === undefined}
          download={"results.csv"}
        >
          Download CSV
        </Button>
      </ButtonGroup>
      <Stack spacing={4}>
        {showLoading ? <CircularProgress /> : <div />}
        {apiResponse?.photo_metrics?.map((metrics, i) => (
          <Paper key={i}>
            <Grid container spacing={4} padding={3}>
              <Grid item>
                <img
                  src={metrics.annotated_file}
                  alt={metrics.annotated_file}
                  width={500}
                />
              </Grid>
              <Grid item>
                <Stack spacing={1}>
                  <p>File Info</p>
                  <Table>
                    <TableBody>
                      <TableRow>
                        <TableCell>File</TableCell>
                        <TableCell>{metrics.file}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Size</TableCell>
                        <TableCell>0 KB</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                  <p>Counts</p>
                  <Table>
                    <TableBody>
                      {metrics.predictions.map((m, j) => (
                        <TableRow key={j}>
                          <TableCell>{m.animal}</TableCell>
                          <TableCell>{m.count}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <ButtonGroup>
                    <Button>Accept</Button>
                    <Button>Make Corrections</Button>
                  </ButtonGroup>
                </Stack>
              </Grid>
            </Grid>
          </Paper>
        ))}
      </Stack>
    </Stack>
  );
}

function useJsonDownloadUrl(
  photo_metrics: Array<PhotoMetrics> | undefined
): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const data = JSON.stringify(photo_metrics || []);
  useEffect(() => {
    if (photo_metrics === undefined) {
      return;
    }

    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    setUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [data, photo_metrics]);
  return url;
}

function useCSVDownloadUrl(
  photo_metrics: Array<PhotoMetrics> | undefined
): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const data: string =
    "File,Animal,Count\n" +
    photo_metrics
      ?.flatMap((metrics) =>
        metrics.predictions.map(
          (prediction) =>
            `${metrics.file},${prediction.animal},${prediction.count}`
        )
      )
      .reduce((a, b) => `${a}\n${b}`);
  useEffect(() => {
    if (photo_metrics === undefined) {
      return;
    }

    const blob = new Blob([data], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    setUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [data, photo_metrics]);
  return url;
}
