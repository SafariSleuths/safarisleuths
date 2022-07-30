import React, { useEffect, useState } from "react";
import {
  Button,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  TextField,
} from "@mui/material";
import {
  getCollections,
  postCollection,
  Collection,
} from "../actions/Collections";

export function CollectionSelect(props: {
  collectionID: string;
  setCollectionID: (v: string) => void;
  setUploadedFiles: (v: Array<string> | undefined) => void;
}) {
  const [allCollections, setAllCollections] = useState<
    Array<Collection> | undefined
  >(undefined);

  useEffect(() => {
    if (allCollections === undefined) {
      getCollections().then((val) => setAllCollections(val));
    }
  });

  return (
    <Grid marginTop={2} container>
      <Grid item xs={3}>
        <h4>Choose an existing collection:</h4>
        <InputLabel id="collection">Collections</InputLabel>
        <Select
          size={"small"}
          value={allCollections !== undefined ? props.collectionID : ""}
          label="Collections"
          id="collection"
          onChange={(e) => {
            props.setUploadedFiles(undefined);
            props.setCollectionID(e.target.value);
          }}
        >
          {allCollections?.map((collection) => (
            <MenuItem key={collection.id} value={collection.id}>
              {collection.name}
            </MenuItem>
          ))}
        </Select>
      </Grid>
      <Grid item xs={9}>
        <h4>Create a new collection:</h4>
        <NewCollectionForm
          allCollections={allCollections || []}
          setAllCollections={setAllCollections}
          setCollectionID={props.setCollectionID}
          setUploadedFiles={props.setUploadedFiles}
        />
      </Grid>
    </Grid>
  );
}

function NewCollectionForm(props: {
  allCollections: Array<Collection>;
  setAllCollections: (v: Array<Collection>) => void;
  setCollectionID: (v: string) => void;
  setUploadedFiles: (v: Array<string> | undefined) => void;
}) {
  const [canSubmit, setCanSubmit] = React.useState(false);
  let newCollectionName = "";

  return (
    <Grid container spacing={1}>
      <Grid item>
        <TextField
          label={"Name"}
          onChange={(e) => {
            if (e.target.value !== "") {
              newCollectionName = e.target.value;
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
            postCollection(newCollectionName).then((collection) => {
              props.setAllCollections([
                ...(props.allCollections || []),
                collection,
              ]);
              props.setUploadedFiles(undefined);
              props.setCollectionID(collection.id);
            });
          }}
        >
          Submit
        </Button>
      </Grid>
    </Grid>
  );
}
