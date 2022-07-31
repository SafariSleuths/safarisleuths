import {
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
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>A unique ID for the annotation.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>file_name</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>url</Typography>
            </TableCell>
            <TableCell>Location of the original file.</TableCell>
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
              <Typography fontFamily={"monospace"}>predicted_name</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>The predicted name of the individual animal.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>species</Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>string</Typography>
            </TableCell>
            <TableCell>The predicted species of the animal.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>
                species_confidence
              </Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>float</Typography>
            </TableCell>
            <TableCell>The confidence of the species prediction.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>
                annotated_file_name
              </Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>url</Typography>
            </TableCell>
            <TableCell>Location of the annotated image.</TableCell>
          </TableRow>
          <TableRow>
            <TableCell>
              <Typography fontFamily={"monospace"}>
                cropped_file_name
              </Typography>
            </TableCell>
            <TableCell>
              <Typography fontFamily={"monospace"}>url</Typography>
            </TableCell>
            <TableCell>Location of the cropped image.</TableCell>
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
    </Stack>
  );
}
