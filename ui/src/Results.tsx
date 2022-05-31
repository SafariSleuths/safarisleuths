import React, { useEffect, useState } from "react";
import {
  Box,
  Button,
  ButtonGroup,
  CircularProgress,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";

export function Results(props: { sessionID: string }) {
  const [predictionResponse, setPredictionResponse] = useState<
    PredictionResponse | undefined
  >(undefined);

  const [showLoading, setShowLoading] = useState(false);

  function getPredictions() {
    setPredictionResponse(undefined);
    setShowLoading(true);
    fetchPredictions({ session_id: props.sessionID }).then((data) => {
      setPredictionResponse(data);
      setShowLoading(false);
    });
  }

  const jsonDownloadUrl = useJsonDownloadUrl(predictionResponse?.results);
  const csvDownloadUrl = useCSVDownloadUrl(predictionResponse?.results);

  return (
    <Stack spacing={2}>
      <h2>Prediction Results</h2>
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

      {showLoading ? (
        <Box alignContent={"center"} width={"100%"}>
          <CircularProgress />
        </Box>
      ) : (
        <Stack spacing={4}>
          <h3>Prediction Summary</h3>
          <PredictionSummary summary={predictionResponse?.summary} />
          <h3>Image Breakdown</h3>
          {predictionResponse?.results.map((imagePredictions) => (
            <ImageBreakdown imagePredictions={imagePredictions} />
          ))}
        </Stack>
      )}
    </Stack>
  );
}

function PredictionSummary(props: {
  summary: Array<AnimalSummary> | undefined;
}) {
  return (
    <Paper elevation={2}>
      <Stack padding={2}>
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
            {props.summary?.map((summary, i) => (
              <TableRow>
                <TableCell>{i + 1}</TableCell>
                <TableCell>{summary.animal_id}</TableCell>
                <TableCell>{summary.species}</TableCell>
                <TableCell>{summary.appearances}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Stack>
    </Paper>
  );
}

function ImageBreakdown(props: { imagePredictions: ImagePredictions }) {
  return (
    <Paper elevation={2}>
      <Stack marginX={2}>
        <h4>{props.imagePredictions.file}</h4>
        <Grid container spacing={4} padding={2}>
          <Grid item>
            <Stack spacing={1}>
              <a href={"localhost:5000" + props.imagePredictions.annotated_url}>
                <img
                  src={props.imagePredictions.annotated_url}
                  alt={props.imagePredictions.annotated_url}
                  width={500}
                />
              </a>
              <ButtonGroup fullWidth={true}>
                <Button>Accept</Button>
                <Button>Make Corrections</Button>
              </ButtonGroup>
            </Stack>
          </Grid>
          <Grid item>
            <Stack spacing={1}>
              <h4>Predictions</h4>
              <Table size={"small"}>
                <TableHead>
                  <TableRow>
                    <TableCell>#</TableCell>
                    <TableCell>Animal ID</TableCell>
                    <TableCell>Species</TableCell>
                    <TableCell>Confidence</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {props.imagePredictions.predictions.map((m, i) => (
                    <TableRow key={i}>
                      <TableCell>{i + 1}</TableCell>
                      <TableCell>{m.animal_id}</TableCell>
                      <TableCell>{m.species}</TableCell>
                      <TableCell>
                        {(m.boxes[0].confidence * 100).toLocaleString()} %
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Stack>
          </Grid>
        </Grid>
      </Stack>
    </Paper>
  );
}

function useJsonDownloadUrl(
  predictions: Array<ImagePredictions> | undefined
): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const data = JSON.stringify(predictions || []);
  useEffect(() => {
    if (predictions === undefined) {
      return;
    }

    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    setUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [data, predictions]);
  return url;
}

function useCSVDownloadUrl(
  photo_metrics: Array<ImagePredictions> | undefined
): string | undefined {
  const [url, setUrl] = useState<string | undefined>(undefined);
  const data: string =
    "File,AnimalID,Species\n" +
    photo_metrics
      ?.flatMap((metrics) =>
        metrics.predictions.map(
          (prediction) =>
            `${metrics.file},${prediction.animal_id},${prediction.species}`
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

export interface BoundingBox {
  start: Array<number>;
  end: Array<number>;
  confidence: number;
  label: string;
  species: string;
  animal_id: number;
}

export interface AnimalPrediction {
  species: string;
  animal_id: number;
  boxes: Array<BoundingBox>;
}

export interface ImagePredictions {
  file: string;
  annotated_url: string;
  predictions: Array<AnimalPrediction>;
}

interface AnimalSummary {
  animal_id: number;
  species: string;
  appearances: number;
}

interface PredictionResponse {
  status: string;
  summary: Array<AnimalSummary>;
  results: Array<ImagePredictions>;
}

export interface PredictionRequest {
  session_id: string;
}

export function fetchPredictions(
  req: PredictionRequest
): Promise<PredictionResponse> {
  return fetch("/api/v1/predict", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(req),
  })
    .then((resp) => resp.json())
    .catch((reason) => console.log(reason));
}
