"""
Run a Flask RestApi exposing the pre-trained Yolov5 model
"""

import argparse
import io 
import torch
from flask import Flask, redirect, url_for, request, send_file
import pandas as pd
from PIL import Image
from io import StringIO, BytesIO
import boto3


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Define the access points for the S3 bucket
app.config['S3_BUCKET'] = "animal-id-sagemaker"
app.config['S3_KEY'] = ""
app.config['S3_SECRET'] = ""
app.config['S3_LOCATION'] = 'http://{}.s3.amazonaws.com/'.format(app.config['S3_BUCKET'])

# Define the boto3 client
client = boto3.client('s3',aws_access_key_id=app.config['S3_KEY'], 
aws_secret_access_key="",
region_name= 'us-east-1')

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
      cropped = im.crop(bbox)
      image_buffer = BytesIO()
      cropped.save(image_buffer, format=im.format)
      value = image_buffer.getvalue()
      md = hashlib.md5(value).digest()
      img_md5 = base64.b64encode(md).decode('utf-8')
      client.put_object(ContentMD5=img_md5, Body=image_buffer, Bucket=app.config['S3_BUCKET'], 
      Key='website-data/cropped_images/{}'.format(str(idx) + '_' + fname))

@app.route('/predict', methods=['PUT'])
def predict():
    # Get the uploaded files
    files = request.files.getlist('files[]')
    
    for file in files:
        # Get the filename
        fname = file.filename
        # Convert the image into bytes and load into PIL Image
        img_bytes = f.read()
        im = Image.open(io.BytesIO(im_bytes))
        # Send the results to the model for prediction
        results = model(img, size=640)
        # Create a csv file from the predictions and save to S3 storage
        data = results.pandas().xyxy[0]
        # Send the annotations to S3 storage
        s3methods.upload_annotations(fname, data)
        # Save the cropped images to S3 storage
        s3methods.crop_img_upload(fname, im, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask api exposing yolov5 model')
    parser.add_argument("--port", default=5000, type=int, help='port number')
    args = parser.parse_args()
    # Use force reload to cache
    model = torch.hub.load('ultralytics/yolov5', 'custom', 'best.onnx', autoshape=True, force_reload=True)
    app.run(host='0.0.0.0', port=args.port)
