import React, { useEffect, useState } from "react";
import "./App.css";
import {
  Box,
  Button,
  ButtonGroup,
  FormControl,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableRow,
} from "@mui/material";
import { ApiResponse, fetchPhotoMetrics, PhotoMetrics } from "./ApiResponse";

function App() {
  return (
    <Box padding={2}>
      <h1>Zebra Counter</h1>
      <Grid container spacing={2}>
        <Grid item xs={3}>
          <Box width={300}>
            <UploadMenu />
          </Box>
        </Grid>
        <Grid item xs={9}>
          <Results />
        </Grid>
      </Grid>
    </Box>
  );
}

function UploadMenu() {
  const uploadedPhotos = [
    "/data/inputs/0/zebra-1.jpeg",
    "/data/inputs/0/zebra-2.jpeg",
    "/data/inputs/0/zebra-3.jpeg",
  ];

  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);

  function uploadPhotos() {}

  return (
    <Stack spacing={2}>
      <h2>Source Files</h2>
      <FormControl>
        <input
          multiple={true}
          accept={"image/jpeg,image/png"}
          type={"file"}
          onChange={(e) => setSelectedFiles(e.target.files)}
        />
        <Button disabled={selectedFiles == null} onClick={uploadPhotos}>
          Upload Photos
        </Button>
      </FormControl>
      <Stack
        maxHeight={"100vh"}
        style={{ overflowY: "scroll", overflowX: "visible" }}
      >
        {uploadedPhotos.map((src, i) => (
          <Stack alignItems={"center"} key={i}>
            <p>{src}</p>
            <img src={src} alt={src} width={250} />
            <Button style={{ width: 250 }}>Delete</Button>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}

function Results() {
  const files = ["zebra-1.jpeg", "zebra-2.jpeg", "zebra-3.jpeg"];

  const [apiResponse, setApiResponse] = useState<ApiResponse | undefined>(
    undefined
  );

  function getPredictions() {
    setApiResponse(undefined);
    fetchPhotoMetrics({ files }).then((data) => setApiResponse(data));
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

export default App;
