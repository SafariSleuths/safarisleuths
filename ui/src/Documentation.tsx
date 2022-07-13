import {
  Box,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

export function Documentation() {
  return (
    <Stack justifyContent={"center"} maxWidth={"800"}>
      <h3>Data Types</h3>
      <h4>Annotation</h4>
      <p>
        The annotation format is similar to the COCO format for object
        detection, but we've added additional fields to capture the individual
        animal predictions.
      </p>
      <Table size={"small"}>
        <TableHead>
          <TableRow>
            <TableCell>
              <strong>Field</strong>
            </TableCell>
            <TableCell>
              <strong>Type</strong>
            </TableCell>
            <TableCell>
              <strong>Summary</strong>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>id</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>integer</Typography>
            </TableCell>
            <TableCell>Unique annotation id.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>image_id</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>integer</Typography>
            </TableCell>
            <TableCell>Unique image id.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>bbox</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>Array of floats</Typography>
            </TableCell>
            <TableCell>Bounding box coordinates: [x,y,width,height].</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>name</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>
              The name of the individual animal with the highest prediction
              confidence.
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>species</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>Species of the animal.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>confidence</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>float</Typography>
            </TableCell>
            <TableCell>
              The prediction confidence of the individual prediction.
            </TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>predictions</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>
                Array of IndividualPredictions
              </Typography>
            </TableCell>
            <TableCell>Top 5 individual predictions.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>image_src</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>url</Typography>
            </TableCell>
            <TableCell>Link to the original image.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>
                annotated_image_src
              </Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>url</Typography>
            </TableCell>
            <TableCell>Link to the annotated image.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>reviewed</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>boolean</Typography>
            </TableCell>
            <TableCell>Has this annotation been manually reviewed?</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>ignored</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>boolean</Typography>
            </TableCell>
            <TableCell>Should this image be ignored?</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>location</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>Dictionary</Typography>
            </TableCell>
            <TableCell>Geolocation data, if available.</TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <h4>IndividualPrediction</h4>
      <p>This is the a prediction of an individual animal within an image.</p>
      <Table size={"small"}>
        <TableHead>
          <TableRow>
            <TableCell>
              <strong>Field</strong>
            </TableCell>
            <TableCell>
              <strong>Type</strong>
            </TableCell>
            <TableCell>
              <strong>Summary</strong>
            </TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>name</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>Unique name of the predicted individual.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>confidence</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>float</Typography>
            </TableCell>
            <TableCell>The confidence score for this prediction.</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </Stack>
  );
}
