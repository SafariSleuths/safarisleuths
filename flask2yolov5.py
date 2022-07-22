"""
Run a Flask RestApi exposing the pre-trained Yolov5 model
"""

import argparse

import io
import os
from typing import List, Tuple, NamedTuple, Optional, TypedDict, Any, Dict

import PIL.Image
import pandas
import torch
import torchvision
from flask import Flask, request
import pandas as pd
from PIL import Image
from io import StringIO
import boto3
# Import the py file to generate predictions
from torch import nn

import indiv_rec
from joblib import load

from predict_bounding_boxes import predict_bounding_boxes, read_images, YolovPrediction, BoundingBox
from predict_individual import predict_individuals_from_yolov_predictions, IndividualPrediction
from s3_client import s3_bucket

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Define the access points for the S3 bucket
app.config['S3_BUCKET'] = "animal-id-sagemaker"
app.config['S3_KEY'] = ""
app.config['S3_SECRET'] = ""
app.config['S3_LOCATION'] = f'http://{app.config["S3_BUCKET"]}.s3.amazonaws.com/'

# Define the boto3 client
client = boto3.client('s3', aws_access_key_id=app.config['S3_KEY'],
                      aws_secret_access_key=app.config['S3_SECRET'],
                      region_name='us-east-1')


def upload_annotations(fname, df):
    """A helper function to write annotations to S3 storage"""
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_object_name = fname + '.csv'
    client.put_object(Body=csv_buffer.getvalue(), Bucket=app.config['S3_BUCKET'],
                      Key='website-data/image_predictions/{}'.format(s3_object_name))


def cropped_imgs_s3_individuals(df):
    """
    Accepts a dataframe of individual predictions
    and moves the corresponding cropped images to their S3 training folders.
    """
    for idx, row in df.iterrows():
        # Get the species, predicted individual id of the animal, and image name
        species = row['name']
        animal_id = row['predicted_labels']
        img_name = row['image']
        copy_source = {
            'Bucket': app.config['S3_BUCKET'],
            'key': f'/website-data/cropped_images/{row["name"]}/{img_name}'
        }
        if species == 'Crocuta_crocuta':
            # Copy the image to the individual image folder to enable classifier retraining
            s3_bucket.copy(
                copy_source,
                f'/hyena.coco/processed/train/{animal_id}/{img_name}'
            )
        elif species == 'Panthera_pardus':
            s3_bucket.copy(
                copy_source,
                f'/leopard.coco/processed/train/{animal_id}/{img_name}'
            )
        elif species == 'Giraffa_tippelskirchi':
            s3_bucket.copy(
                copy_source,
                f'/great_zebra_giraffe/individual_recognition/train/{animal_id}/{img_name}'
            )
        # Copy the image to the all individuals folder to enable retraining of the embeddings
        s3_bucket.copy(copy_source, f'/all_animal_recognition/train/{img_name}')


class Annotation(NamedTuple):
    file_name: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    bbox: Optional[BoundingBox]
    bbox_confidence: Optional[float]
    predicted_species: Optional[str]
    predicted_name: Optional[str]

    def asdict(self) -> Dict[str, Any]:
        data = self._asdict()
        data['bbox'] = self.bbox._asdict()
        return data


INPUTS_PATH = 'website-data/inputs'


@app.route('/predict', methods=['PUT'])
def predict():
    session_id = 'testing'
    # Get the uploaded files
    files = request.files.getlist('files[]')
    input_file_names = []
    for file in files:
        file_name = f'{INPUTS_PATH}/{session_id}/{file.name}'
        file.save(file_name)
        input_file_names.append(file.name)

    yolov_predictions = []
    for input_image in read_images(input_file_names):
        yolov_predictions + predict_bounding_boxes(input_image, session_id)

    individual_predictions = predict_individuals_from_yolov_predictions(yolov_predictions)

    yolov_predictions.sort(key=lambda p: p.cropped_file_name)
    individual_predictions.sort(key=lambda p: p.cropped_file_name)
    annotations = []
    for yolov_prediction, individual_prediction in zip(yolov_predictions, individual_predictions):
        annotations.append(Annotation(
            file_name=yolov_prediction.file_name,
            annotated_file_name=yolov_prediction.annotated_file_name,
            cropped_file_name=yolov_prediction.cropped_file_name,
            bbox=yolov_prediction.bbox,
            bbox_confidence=yolov_prediction.bbox_confidence,
            predicted_species=yolov_prediction.predicted_species,
            predicted_name=individual_prediction.individual_name,
        ))
    return {'annotations': [a._asdict() for a in annotations]}


def x():
    batch_size = 128
    len_uploaded_images = 60
    ratio = 2
    total_images = ((int(len_uploaded_images * 3) // 128) + 1) * 128
    len_old_images = total_images - len_uploaded_images


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask api exposing yolov5 model')
    parser.add_argument("--port", default=5000, type=int, help='port number')
    args = parser.parse_args()
    app.run(host='0.0.0.0', port=args.port)
