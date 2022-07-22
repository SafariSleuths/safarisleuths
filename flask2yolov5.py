"""
Run a Flask RestApi exposing the pre-trained Yolov5 model
"""

import argparse
import base64
import hashlib
import io
import os
from typing import List, Tuple

import PIL.Image
import torch
import torchvision
from flask import Flask, redirect, url_for, request, send_file
import pandas as pd
from PIL import Image
from io import StringIO, BytesIO
import boto3
# Import the py file to generate predictions
from torch import nn

import indiv_rec
from joblib import load

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


def yolov2coco(row, og_w, og_h):
    """Converts the Yolov predictions to Coco format, scaled to the input image size"""

    # Scale the Yolov predictions to normalize
    x1 = (row['xmin'] / 640) * og_w
    y1 = (row['ymin'] / 640) * og_h
    x2 = (row['xmax'] / 640) * og_w
    y2 = (row['ymax'] / 640) * og_h
    # Multiply by the original input image with and height
    row['x_coco'] = x1
    row['y_coco'] = y1
    row['w_coco'] = x2 - x1
    row['h_coco'] = y2 - y1
    return row


def upload_annotations(fname, df):
    """A helper function to write annotations to S3 storage"""
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_object_name = fname + '.csv'
    client.put_object(Body=csv_buffer.getvalue(), Bucket=app.config['S3_BUCKET'],
                      Key='website-data/image_predictions/{}'.format(s3_object_name))


def crop_img_upload(fname, im, df):
    """Crops an image to its bounding box and saves the cropped image to S3"""
    for idx, row in df.iterrows():
        bbox = [row['xmin'], row['ymin'], row['xmax'], row['ymax']]
        # Get the predicted class to save to that folder in S3 and locally
        pred_class = row['name']
        # Crop the image to the bounding box
        cropped = im.crop(bbox)
        # Save the image locally to its predicted class folder using the original filename
        # and the index to indicate the bounding box being saved.
        name2save = row['index'] + '_' + fname
        cropped.save(f'/{pred_class}/{name2save}')
        # Convert the image to bytes and save to S3
        image_buffer = BytesIO()
        cropped.save(image_buffer, format=im.format)
        s3_bucket.upload_file(
            f'/{pred_class}/{name2save}',
            f'website-data/cropped_images/{pred_class}/{str(idx) + "_" + fname}'
        )


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


@app.route('/predict', methods=['PUT'])
def predict():
    # Get the uploaded files
    files = request.files.getlist('files[]')
    pred_df = predict_bounding_boxes(files)
    return predict_individual(pred_df)


def predict_individual(pred_df):
    # Load the pre-trained embeddings from the previously trained model backbone
    resnet18_new = torchvision.models.resnet18()
    backbone_new = nn.Sequential(*list(resnet18_new.children())[:-1])
    ckpt = torch.load('resnet18embed.pth')
    backbone_new.load_state_dict(ckpt['resnet18_parameters'])
    # Specify if the embeddings should be evaluated on cpu or gpu
    device = torch.device('cuda' if torch.cuda_is_available() else 'cpu')
    # Instantiate the species dataframes as None; None will be replaced if their folders are non-empty
    hyena_preds, leopard_preds, giraffe_preds = None, None, None
    if len(os.listdir('/Crocuta_crocuta')) != 0:
        # Load the animal specific classifiers
        hyena_clf = load('hyena_knn.joblib')
        hyena_preds = indiv_rec.predict_individuals('/Crocuta_crocuta', backbone_new, device, hyena_clf)
        # Retrieve the saved file of integer labels to string ids and add the string ids to the dataframe
        hyena_id = load('hyena_id_map.joblib')
        hyena_preds['individual_id'] = hyena_preds.apply(lambda row: hyena_id.get(row['predicted_labels']), axis=1)
    if len(os.listdir('/Panthera_pardus')) != 0:
        leopard_clf = load('leopard_knn.joblib')
        leopard_preds = indiv_rec.predict_individuals('/Panthera_pardus', backbone_new, device, leopard_clf)
        leopard_id = load('leopard_id_map.joblib')
        leopard_preds['individual_id'] = leopard_preds.apply(lambda row: leopard_id.get(row['predicted_labels']),
                                                             axis=1)
    if len(os.listdir('/Giraffa_tippelskirchi')) != 0:
        giraffe_clf = load('giraffe_knn.joblib')
        giraffe_preds = indiv_rec.predict_individuals('/Giraffa_tippelskirchi', backbone_new, device, giraffe_clf)
        giraffe_id = load('giraffe_id_map.joblib')
        giraffe_preds['individual_id'] = giraffe_preds.apply(lambda row: giraffe_id.get(row['predicted_labels']),
                                                             axis=1)
    # Concatenate the individual predictions to a single dataframe
    indiv_preds = pd.concat([hyena_preds, leopard_preds, giraffe_preds], axis=0, ignore_index=True)
    # Perform a left join of the Yolov predictions to the individual predictions to keep images
    # where a Yolov prediction failed to be made
    pred_df = pred_df.merge(indiv_preds, on='image', how='left')
    return pred_df


def x():
    batch_size = 128
    len_uploaded_images = 60
    ratio = 2
    total_images = ((int(len_uploaded_images * 3) // 128) + 1) * 128
    len_old_images = total_images - len_uploaded_images


def predict_bounding_boxes(files):
    # Create several lists that will become the columns of the annotations file
    data_dict = {'filename': [], 'index': [], 'x': [], 'y': [], 'w': [], 'h': [],
                 'confidence': [], 'class': [], 'name': []}
    pil_images: List[Tuple[str, PIL.Image]] = []
    for file in files:
        fname = file.filename
        im_bytes = file.read()
        im = Image.open(io.BytesIO(im_bytes))
        pil_images.append((fname, im))
    images_pre_model_input: List[Tuple[str, PIL.Image, int, int]] = []

    for fname, im in pil_images:
        # Get the dimensions of the original image
        width, height = im.size
        # Resize the image to the input dimensions for the pre-trained Yolov5 small
        im = im.resize((640, 640))
        images_pre_model_input.append((fname, im, height, width))

    for fname, im, height, width in images_pre_model_input:
        results = model(im, size=640)
        # Create a csv file from the predictions and save to S3 storage
        data = results.pandas().xyxy[0]
        # Reset the index
        data.reset_index()
        # If a prediction is make, convert the results to Coco format
        if len(data) >= 1:
            data_dict['filename'].extend([fname] * len(data))
            # Convert the annotations to Coco format
            data = data.apply(yolov2coco, width, height, axis=1)
            # Add the Coco bb values, confidence, name, and class to the dict
            data_dict['index'].extend(data['index'].tolist())
            data_dict['x'].extend(data['x_coco'].tolist())
            data_dict['y'].extend(data['y_coco'].tolist())
            data_dict['w'].extend(data['w_coco'].tolist())
            data_dict['h'].extend(data['h_coco'].tolist())
            data_dict['confidence'].extend(data['confidence'].tolist())
            data_dict['class'].extend(data['class'].tolist())
            data_dict['name'].extend(data['name'].tolist())
            # Save the cropped images to S3 storage and to a local folder
            crop_img_upload(fname, im, data)
        else:
            data_dict['filename'].append(fname)
            data_dict['index'].append(None)
            data_dict['x'].append(None)
            data_dict['y'].append(None)
            data_dict['w'].append(None)
            data_dict['h'].append(None)
            data_dict['confidence'].append(None)
            data_dict['class'].append(None)
            data_dict['name'].append(None)

    # Create a pandas dataframe from the Yolov predictions
    pred_df = pd.DataFrame(data_dict)
    # Add a new column to represent the unique identifier for every cropped image
    pred_df['image'] = pred_df.apply(lambda row: str(row.index) + '_' + row.filename)
    return pred_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask api exposing yolov5 model')
    parser.add_argument("--port", default=5000, type=int, help='port number')
    args = parser.parse_args()
    # Use force reload to cache
    model = torch.hub.load('ultralytics/yolov5', 'custom', 'frozen_backbone_coco_unlabeled_best.onnx', autoshape=True,
                           force_reload=True)
    app.run(host='0.0.0.0', port=args.port)
