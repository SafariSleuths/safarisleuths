# w210-capstone
Determining Species Count in Protected Areas Through Image Recognition.

## Overview

Poaching continues to pose a threat to the survival of endangered species, even on protected land. Tracking individual animals and maintaining species counts is essential in combating this threat, by allowing conservationists to determine the impact of natural changes vs poaching impact and deciding where and when to deploy resources to protect the animals. However, current methods of identifying and counting individual animals are time-consuming and limit the ability to protect them in a timely manner.

Our solution to this problem is to automate the process of identifying individual animals in camera-trap still images, allowing conservationists to more quickly check and correct individual animal labels if necessary. Using publicly available datasets for individual animal identification, we successfully implemented models to predict more than 800 unique animals across 3 species and developed an interactive tool to allow users to view predicted labels and make corrections as needed.

## Training Data

For the datasets, we were able to retrieve a handful of images for each animal in relation to Hyenas, Leopards, and Giraffes. These images were posted into an S3 bucket along with their annotations that include the coordinates for their bounding boxes and individual IDs. We then further divided the individual animal images into a set of training, validation, and testing folders that were used for our modeling process.

## Modeling

The modeling process starts with the images that have been uploaded into the 3 distinct folders of train, validation, and test with a configuration file that will have the labels for classification. These images are resized to a consistent size and passed into the YOLOv5 pipeline along with the location to the images and the coordinate annotations and weights applied. After training, the model can detect the location of the animals within an image with a confidence score, and can crop the animals from the image. The cropped images are passed into the individual detection phase. We train a model to produce image embeddings by using SimCLR v1 to fine-tune the resnet18 embeddings. The embeddings are used as features to train an individual recognition classifier. Lastly, we train KNN classifiers with a nearest neighbor of 1 to assign individual labels.

## Modeling Results

At this stage, we are presenting validation set results and can see that YOLOv5 has achieved high accuracy, recall, and precision scores as well as low losses. We chose these metrics since they are commonly reported in the literature. Additionally, since the distribution of training images between species is imabalanced, including precision and recall better reflects model performance than accuracy alone. Here, bounding box loss is the errors between predicted and actual bounding boxes, object loss – errors in whether or not an object is detected inside a bounding box, and classification loss (the squared error of the conditional probabilities of each class). The model fails to produce predictions for 2% of validation images; however, when a prediction is produced, the predicted classes are highly accurate, with only 7 images out of more than a 1k having an incorrect class predicted. For our giraffe species, all images were accurately classified, which may be due to the YOLOv5 model being pre-trained on the general class giraffes; hyenas and leopards were not pre-training classes.

For the individual recognition models, we are reporting top-1 accuracy scores, since the predicted label is what is displayed to the web API user and due to its use in prior studies on individual identification. We are also reporting weighted precision and recall scores, due to the imbalance in the representation of individual animals in our datasets. Although there is room for improvement in our top-1 accuracy scores, the classifiers are fairly accurate, given the highly-multiclass nature of our predictions (431 unique leopards; 256 hyenas; 151 giraffes) and when considering that many animals had 10 or fewer training images. When analyzing classifier performance, we see that for hyenas and leopards, the bulk of classification errors occur when the animal had between 5 and 10 training images; giraffes vary, but most animals in that dataset had <= 10 training images.

## Launching the Application

Here is the link to the front end UI: https://groups.ischool.berkeley.edu/safari_sleuths/

And the steps on how to execute the end-to-end modeling process:

1. Create a new collection or choose an existing collection
2. Upload photo(s)
3. Compute the prediction results
4. Accept, reject, or edit the annotations
5. Retrain the model to recompute the prediction results
