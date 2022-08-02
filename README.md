# w210-capstone

Determining Species Count in Protected Areas Through Image Recognition.

## Overview

Poaching continues to pose a threat to the survival of endangered species, even on protected land. Tracking individual
animals and maintaining species counts is essential in combating this threat, by allowing conservationists to determine
the impact of natural changes vs poaching impact and deciding where and when to deploy resources to protect the animals.
However, current methods of identifying and counting individual animals are time-consuming and limit the ability to
protect them in a timely manner.

Our solution to this problem is to automate the process of identifying individual animals in camera-trap still images,
allowing conservationists to more quickly check and correct individual animal labels if necessary. Using publicly
available datasets for individual animal identification, we successfully implemented models to predict more than 800
unique animals across 3 species and developed an interactive tool to allow users to view predicted labels and make
corrections as needed.

## Training Data

For the datasets, we were able to retrieve a handful of images for each animal in relation to Hyenas, Leopards, and
Giraffes. These images were posted into an S3 bucket along with their annotations that include the coordinates for their
bounding boxes and individual IDs. We then further divided the individual animal images into a set of training,
validation, and testing folders that were used for our modeling process.

## Modeling

The modeling process starts with the images that have been uploaded into the 3 distinct folders of train, validation,
and test with a configuration file that will have the labels for classification. These images are resized to a
consistent size and passed into the YOLOv5 pipeline along with the location to the images and the coordinate annotations
and weights applied. After training, the model can detect the location of the animals within an image with a confidence
score, and can crop the animals from the image. The cropped images are passed into the individual detection phase. We
train a model to produce image embeddings by using SimCLR v1 to fine-tune the resnet18 embeddings. The embeddings are
used as features to train an individual recognition classifier. Lastly, we train KNN classifiers with a nearest neighbor
of 1 to assign individual labels.

## Modeling Results

Our YOLOv5 model achieves low training and validation loss scores in the 3 types of losses used to evaluate model
performance: bounding box loss (the errors between predicted and actual bounding boxes), object loss (errors in whether
or not an object is detected inside a bounding box), and classification loss (the squared error of the conditional
probabilities of each class). Based upon test image performance, YOLOv5 achieves high accuracy, recall, and precision
scores. We chose these metrics since they are commonly reported in the literature and reported them by species, due to
the imbalance in the representation of the 3 species in our dataset. The model fails to produce predictions for 2% of
test images; however, when a prediction is produced, the predicted classes are highly accurate, with only 9 images out
of more than 1k having an incorrect class predicted. For our giraffe species, all images were accurately classified,
which may be due to the Yolov5 model being pre-trained on the general class giraffes; hyenas and leopards were not seen
in the pre-training classes.

## Launching the Browser-based Application

We provide a browser-based application that allows you to run predictions and retrain the model. The app requires a
redis database, which you can launch using docker-compose.

```shell
git checkout git@github.com:SafariSleuths/safarisleuths.git
cd safarisleuths
docker-compose up
```

The app server is written using Flask and can be launched as a normal flask app. The server requires pytorch and does
not behave well in a docker container, so it is better to launch natively.

```shell
pip install -r requirements.txt
python app.py
```

The following environment variables are supported:

| Name           | Description                       | Default   |
|----------------|-----------------------------------|-----------|
| APP_HOST       | Host address for the api server.  | localhost |
| APP_PORT       | Port for the api server.          | 5000      |
| REDIS_HOST     | Host address of the redis server. | localhost |
| REDIS_PORT     | Port of the redis server.         | 6379      |
| S3_ACCESS_KEY  | Optional S3 access key.           | `None`    |
| S3_SECRET_KEY  | Optional S3 secret key.           | `None`    |
| S3_BUCKET_NAME | Optional S3 bucket name.          | `None`    |

### Prediction Results

All prediction results are stored locally in a directory named `website-data`.

### Training Data

The API server looks for training data in a local directory named `training_data` and expects the images organized in
this format:`training_data/cropped/ANIMAL_NAME/FILE_NAME.jpg'`. Images for retraining should be cropped to only include
the animal.

### S3 Support

If an S3 access key, secret key, and bucket are provided, then results will be uploaded to the bucket. Prediction
results are uploaded to the prefix `BUCKET_NAME/website-data/outputs/`. New training data is uploaded to the
prefix `BUCKET_NAME/training_data/`.
