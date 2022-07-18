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
aws_secret_access_key=app.config['S3_SECRET'],
region_name= 'us-east-1')

def yolov2coco(row, og_w, og_h, ):
    """Converts the Yolov predictions to Coco format, scaled to the input image size"""

    # Scale the Yolov predictions to normalize
    x1 = (row['xmin']/640)*og_w
    y1 = (row['ymin']/640)*og_h
    x2 = (row['xmax']/)*og_w
    y2 = (row)['ymax']/)*og_h
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
      # Get the predicted class to save to that folder
      pred_class = row['name']
      cropped = im.crop(bbox)
      image_buffer = BytesIO()
      cropped.save(image_buffer, format=im.format)
      value = image_buffer.getvalue()
      md = hashlib.md5(value).digest()
      img_md5 = base64.b64encode(md).decode('utf-8')
      client.put_object(ContentMD5=img_md5, Body=image_buffer, Bucket=app.config['S3_BUCKET'], 
      Key='website-data/cropped_images/{}/{}'.format(pred_class, str(idx) + '_' + fname))

@app.route('/predict', methods=['PUT'])
def predict():
    # Get the uploaded files
    files = request.files.getlist('files[]')

    # Create several lists that will become the columns of the annotations file
    data_dict = {'filename': [], 'index': [], 'x': [], 'y': [], 'h': [],
                 'confidence': [], 'class': [], 'name': []}
        
    for file in files:
        # Get the filename
        fname = file.filename
        # Convert the image into bytes and load into PIL Image
        img_bytes = f.read()
        im = Image.open(io.BytesIO(im_bytes))
        # Get the dimensions of the input image
        width, height = im.size
        #Resize the image to the input dimensions for the pre-trained Yolov5 small
        im = im.resize((640,640))
        # Send the results to the model for prediction
        results = model(img, size=640)
        # Create a csv file from the predictions and save to S3 storage
        data = results.pandas().xyxy[0]
        # Store the image filename regardless of predictions being produced
        data_dict['filename'].append(fname)
        # If a prediction is make, convert the results to Coco format
        if len(data) >= 1:
            # Convert the annotations to Coco format
            data = data.apply(yolov2coco, width, height, axis=1)
            data.reset_index()
            # Add the Coco bb values, confidence, name, and class to the dict
            data_dict['index'].extend(data['index'].tolist())
            data_dict['x'].extend(data['x_coco'].tolist())
            data_dict['y'].extend(data['y_coco'].tolist())
            data_dict['w'].extend(data['w_coco'].tolist())
            data_dict['h'].extend(data['h_coco'].tolist())
            data_dict['confidence'].extend(data['confidence'].tolist())
            data_dict['class'].extend(data['class'].tolist())
            data_dict['name'].extend(data['name'].tolist())
            # Save the cropped images to S3 storage
            crop_img_upload(fname, im, data)
        else:
            data_dict['index'].append(None)
            data_dict['x'].append(None)
            data_dict['y'].append(None)
            data_dict['w'].append(None)
            data_dict['h'].append(None)
            data_dict['confidence'].append(None)
            data_dict['class'].append(None)
            data_dict['name'].append(None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask api exposing yolov5 model')
    parser.add_argument("--port", default=5000, type=int, help='port number')
    args = parser.parse_args()
    # Use force reload to cache
    model = torch.hub.load('ultralytics/yolov5', 'custom', 'frozen_backbone_coco_unlabeled_best.onnx', autoshape=True, force_reload=True)
    app.run(host='0.0.0.0', port=args.port)
