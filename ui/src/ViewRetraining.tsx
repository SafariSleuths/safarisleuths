import { Box, List, ListItem } from "@mui/material";

interface RetrainJob {
  job_id: string;
  images_uploaded: boolean;
  training_started: boolean;
}

export function ViewRetraining(props: { sessionID: string }) {
  return (
    <Box>
      <List>
        <ListItem>Images Uploads: ✅</ListItem>
        <ListItem>Training Progress: ✅</ListItem>
      </List>
    </Box>
  );
}
