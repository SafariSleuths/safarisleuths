#!/usr/bin/python
# Libraries for constructing the dataset
import os
import glob
from PIL import Image
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import numpy as np
from sklearn.preprocessing import normalize
import pandas as pd

# Libraries for finding the best fit model and saving it
from sklearn.model_selection import KFold
from sklearn.model_selection import GridSearchCV
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from joblib import dump, load


def prepare_data(path2data):
    """"
    Parameters: a local filepath to training data consisting of subfolders of individual identifiers
    Returns a dataloader object
    """

    # Set the transformation to be applied to the training data
    train_transform = torchvision.transforms.Compose([
        torchvision.transforms.Resize((224, 224)),
        torchvision.transforms.ToTensor(),
        torchvision.transforms.Normalize(mean=[0.485, 0.456,0.406], std=[0.229,0.224,0.225]),
        ])
    
    # Create an dataset object and dataloader objects
    training_dataset = ImageFolder(path2data, transform=train_transform)
    train_dl = DataLoader(training_dataset, batch_size=1, num_workers=4)

    return train_dl


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
        for im, label in dl:
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


def embeddings2model(path2data, embedding_model, device):
    """
    Parameters:
    path2data: a local filepath to training data consisting of subfolders of individual identifiers
    embedding_model: a pre-trained embedding model
    device: whether to train the model on CPU or GPU
    Returns: a fitted model saved to a local folder and a message
    """

    # Create the dataloader object
    train_dl = prepare_data(path2data)

    # Obtain the training data embeddings
    train_embeddings, train_labels = generate_embeddings(embedding_model, device, train_dl)

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
    if 'Crocuta_crocuta' in path2data:
        dump(clf, '/models/hyena_knn_last.joblib')
        print('Retraining of Crocuta crocuta classifier completed. Model saved as hyena_knn_last.joblib.')
    
    elif 'Panthera_pardus' in path2data:
        dump(clf, '/models/leopard_knn_last.joblib')
        print('Retraining of Panthera pardus classifier completed. Model saved as leopard_knn_last.joblib.')

    elif 'Giraffa_tippelskirchi' in path2data:
        dump(clf, '/models/giraffe_knn_last.joblib')
        print('Retraining of Giraffa tippelskirchi classifier completed. Model saved as giraffe_knn_last.joblib.')
    else:
        print('Unavailable species. Please choose to retrain one of the following: Crocuta crocuta, Panthera pardus, or Giraffa tippelskirchi.')