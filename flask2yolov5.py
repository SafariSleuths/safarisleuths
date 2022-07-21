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
# Import the py file to generate predictions
import indiv_rec
from joblib import load

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
      # Get the predicted class to save to that folder in S3 and locally
      pred_class = row['name']
      # Crop the image to the bounding box
      cropped = im.crop(bbox)
      # Save the image locally to its predicted class folder using the original filename and the index to indicate the bounding box being saved
      name2save = row['index'] + '_' + fname
      cropped.save(f'/{pred_class}/{name2save}')
      # Convert the image to bytes and save to S3
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
        # Get the dimensions of the original image
        width, height = im.size
        #Resize the image to the input dimensions for the pre-trained Yolov5 small
        im = im.resize((640,640))
        # Send the results to the model for prediction
        results = model(img, size=640)
        # Create a csv file from the predictions and save to S3 storage
        data = results.pandas().xyxy[0]
        # Store the image filename regardless of predictions being produced
        data_dict['filename'].append(fname)
        # Reset the index
        data.reset_index()
        # If a prediction is make, convert the results to Coco format
        if len(data) >= 1:
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
    # Load the pre-trained embeddings from the previously trained model backbone
    resnet18_new = torchvision.models.resnet18()
    backbone_new = nn.Sequential(*list(resnet18_new.children())[:-1])
    ckpt = torch.load('resnet18embed.pth')
    backbone_new.load_state_dict(ckpt['resnet18_parameters'])

    # Instantiate the species dataframes as None; None will be replaced if their folders are non-empty
    hyena_preds, leopard_preds, giraffe_preds = None, None, None

    if len(os.listdir('/Crocuta_crocuta')) != 0:
        # Load the animal specific classifiers
        hyena_clf = load('hyena_knn.joblib')
        hyena_preds = indiv_rec.predict_individuals('/Crocuta_crocuta', backbone_new, hyena_clf)
        # Retrieve the saved file of integer labels to string ids and add the string ids to the dataframe
        hyena_id = load('hyena_id_map.joblib')
        hyena_preds['individual_id'] = hyena_preds.apply(lambda row: row: hyena_id.get(row['predicted_labels']), axis=1)
    
    if len(os.listdir('/Panthera_pardus')) != 0:
        leopard_clf = load('leopard_knn.joblib')
        leopard_preds = indiv_rec.predict_individuals('/Panthera_pardus', backbone_new, leopard_clf)
        leopard_id = load('leopard_id_map.joblib')
        leopard_preds['individual_id'] = leopard_preds.apply(lambda row: row: leopard_id.get(row['predicted_labels']), axis=1)
    
    if len(os.listdir('/Giraffa_tippelskirchi')) != 0:
        giraffe_clf = load('giraffe_knn.joblib')
        giraffe_preds = indiv_rec.predict_individuals('/Giraffa_tippelskirchi', backbone_new, giraffe_clf)
        giraffe_id = load('giraffe_id_map.joblib')
        giraffe_preds['individual_id'] = giraffe_preds.apply(lambda row: row: giraffe_id.get(row['predicted_labels']), axis=1)

    # Concatenate the individual predictions to a single dataframe
    indiv_preds = pd.concat([hyena_preds, leopard_preds, giraffe_preds, axis=0, ignore_index=True)

    # Perform a left join of the Yolov predictions to the individual predictions to keep images where a Yolov prediction failed to be made
    pred_df = pred_df.merge(indiv_preds, on='image', how='left'))

    return pred_df


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Flask api exposing yolov5 model')
    parser.add_argument("--port", default=5000, type=int, help='port number')
    args = parser.parse_args()
    # Use force reload to cache
    model = torch.hub.load('ultralytics/yolov5', 'custom', 'frozen_backbone_coco_unlabeled_best.onnx', autoshape=True, force_reload=True)
    app.run(host='0.0.0.0', port=args.port)
