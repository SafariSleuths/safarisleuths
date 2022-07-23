#!/usr/bin/python
# Libraries for constructing the dataset
import os
import glob
from PIL import Image
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader, ConcatDataset
import tempfile
from torchvision.datasets import ImageFolder
import numpy as np
from sklearn.preprocessing import normalize
import pandas as pd

# Libraries for finding the best fit model and saving it
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from joblib import dump, load

# Import S3 permissions and the bucket
from s3_client import s3, s3_bucket

class SpeciesOldTrainDataset(Dataset):
    """A custom class to retrieve and transform all of a species' S3 training images"""
    def __init__(self, s3_resource, s3_bucket, species):

        # Set the method for S3 access, the bucket, and the species to be retrained
        self.s3 = s3_resource
        self.bucket = s3_bucket
        self.species = species

        # Set the S3 path to the training folder
        if self.species == 'Crocuta_crocuta':
            self.train_folder = 'hyena.coco/processed/train/'
        elif self.species == 'Panthera_pardus':
            self.train_folder == 'leopard.coco/processed/train/'
        elif species == 'Giraffa_tippelskirchi':
            self.train_folder == 'great_zebra_giraffe/individual_recognition/train/'
        
        # Get the training image paths to retrain the embeddings
        self.files = []
        for obj_sum in self.bucket.objects.filter(Prefix=self.train_folder):
        if obj_sum.key.endswith('.jpg'):
            self.files.append(obj_sum.key)

        # Get the individual animal ids from their file folders
        self.labels = [x.split('/')[-2] for x in self.files]
        # Map the individual animal id labels to integers
        self.animal_int_labels = [x for x in range(len(self.labels))]
        self.class_to_idx = dict(zip(self.labels, self.animal_int_labels))
        # Set the image resize operation
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456,0.406], std=[0.229,0.224,0.225])])

    def __len__(self):
        return len(self.files)
    
    def __getitem__(self, idx):
        # Get the object name to be downloaded
        img_name = self.files[idx]
        # Get the animal string label of the image to be downloaded
        animal = img_name.split('/')[-2]
        # Convert the string label to an integer one
        label = self.class_to_idx[animal]
        # Download the file to a temporary file
        obj = self.bucket.Object(img_name)
        tmp = tempfile.NamedTemporaryFile()
        tmp_name = '{}.jpg'.format(tmp.name)
        with open(tmp_name, 'wb') as f:
            obj.download_fileobj(f)
            f.flush()
            f.close()
            image = Image.open(tmp_name)
        image = self.transform(image)
        return image, label

class LocalImageClassifierDataset(Dataset):
    """A custom dataset for the locally saved images to be used in retraining"""
    def __init__(self, local_img_path, animal_id_map):
        # Get the full file paths of all local images for the re-training
        self.imgs = glob.glob(local_img_path + '/*/*)
        # Set the mapping of their string labels to integers based upon prior S3 images
        self.class_to_idx = animal_id_map
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456,0.406], std=[0.229,0.224,0.225])])

    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        # Get the image path and animal label string
        img_path = self.imgs[idx]
        animal_name = img_path.split('/')[-2]
        # Map the animal string label to an integer one
        img_label = self.class_to_idx[animal_name]
        # Open the image and resize it to the required dimensions for Resnet18
        im = Image.open(img_path).convert('RGB')
        im = self.transform(im)
        return im, img_label


def generate_embeddings(embedding_model, data_loader):
    """
    Parameters:
    embedding_model: a pretrained Resnet 18 backbone
    data_loader: a dataloader object for which to return embeddings and labels
    Returns: a numpy array of embeddings and labels
    """

    # Create lists to hold the embeddings and labels from the dataloader
    embeddings = []
    labels = []

    # Set the device for model training on GPU if possible
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Specify whether the model should run on CPU or GPU
    model = model.to(device)
    # Place the model in evaluation mode
    model.eval()
    with torch.no_grad():
        for im, label in data_loader:
            # Obtain the embedding of each image and add it to the list
            im = im.to(device)
            embed = model(im).flatten(start_dim=1)
            embeddings.append(embed)
            # Save the data labels
            labels.append(label)
    embeddings = torch.cat(embeddings, 0)
    # Set the embeddings to CPU to be able to normalize
    embeddings = embeddings.cpu()
    # Normalize the embeddings
    embeddings = normalize(embeddings)
    return np.array(embeddings), np.array(labels)


def full_classifier_retrain(s3_resource, s3_bucket, species, local_img_path):
    """
    Parameters:
    s3_resource: the method of accessing the S3 bucket
    s3_bucket: the S3 bucket to be used
    species: the species name for classifier retraining
    local_img_path: the path to a local folder of new images for a single species
    Returns: a fitted model saved to a local folder and a message
    """

    # Create the dataset of prior training images and new ones
    old_train_ds = SpeciesOldTrainDataset(s3_resource, s3_bucket, species)

    # Create the new dataset, consisting of new images from only 1 species
    new_train_ds = LocalImageClassifierDataset(local_img_path, old_train_ds.class_to_idx)

    # Concatenate the old and new datasets
    train_ds = ConcatDataset([old_train_ds, new_train_ds])

    # Create a data loader object, but set the batch size to be 1 so that no training examples are dropped
    train_dl = DataLoader(train_ds, batch_size=1, shuffle=True, num_workers=2, drop_last=True)

    # Obtain the training data embeddings
    train_output = generate_embeddings(embedding_model, train_dl)
    train_embeddings = train_output[0]
    train_labels = train_output[1]

    # Use K-fold cross validation to train the classifier since some classes will only have 1 example
    cv = KFold(n_splits=5, random_state=1, shuffle=True)

    # Define the parameter grid for the KNN model to be searched
    knn_param_grid = = [{'pca__n_components': [0.8, 0.9, 0.95, 0.99],
                         'KNN__n_neighbors': [1, 3, 5, 10], 
                         'KNN__weights': ['uniform', 'distance'], 
                         'KNN__metric': ['euclidean', 'manhattan', 'cosine']}]

    # Define the pipe object to use in Grid Search
    pipe_knn = Pipeline([('scaler', StandardScaler()), 
                     ('pca', PCA()),
                     ('KNN', KNeighborsClassifier())])

    # Create a grid search object and parameters to be searched
    knn_grid_search = GridSearchCV(estimator=pipe_knn, param_grid=knn_param_grid, scoring='accuracy', cv=cv)

    # Fit the data to the training data
    knn_grid_search.fit(train_embeddings, train_labels)

    # Get the best estimator from the grid search results
    clf = knn_grid_search.best_estimator_

    # Save the best fit model to the model folder
    if species == 'Crocuta_crocuta':
        dump(clf, '/models/hyena_knn_last.joblib')
        print('Retraining of Crocuta crocuta classifier completed. Model saved as hyena_knn_last.joblib.')
    
    elif species == 'Panthera_pardus':
        dump(clf, '/models/leopard_knn_last.joblib')
        print('Retraining of Panthera pardus classifier completed. Model saved as leopard_knn_last.joblib.')

    elif species == 'Giraffa_tippelskirchi':
        dump(clf, '/models/giraffe_knn_last.joblib')
        print('Retraining of Giraffa tippelskirchi classifier completed. Model saved as giraffe_knn_last.joblib.')