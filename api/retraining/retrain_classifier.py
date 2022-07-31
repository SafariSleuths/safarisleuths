from typing import List, Tuple

import joblib
import numpy as np
import torch
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import normalize
from torch.utils.data import DataLoader

from api.clients.s3_client import s3_bucket
from api.data_models.annotations import Annotation
from api.data_models.species import Species


def generate_embeddings(backbone, data_loader: DataLoader) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parameters:
    backbone: a pretrained Resnet 18 backbone
    data_loader: a dataloader object for which to return embeddings and labels
    Returns: a numpy array of embeddings and labels
    """

    embeddings = []
    labels = []

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = backbone.to(device)
    model.eval()
    with torch.no_grad():
        for image_batch, label_batch in data_loader:
            image_batch = image_batch.to(device)
            embeddings.append(model(image_batch).flatten(start_dim=1))
            labels.append(label_batch.flatten())
    embeddings = torch.cat(embeddings, 0).cpu()
    embeddings = np.array(normalize(embeddings))
    labels = np.array(torch.cat(labels, 0))
    return embeddings, labels


def retrain_classifier_for_species(species: Species, train_embeddings: np.ndarray, train_labels: np.ndarray) -> None:
    # Use K-fold cross validation to train the classifier since some classes will only have 1 example
    cv = KFold(n_splits=5, random_state=1, shuffle=True)

    # Define the parameter grid for the KNN model to be searched
    knn_param_grid = [{
        'pca__n_components': [0.8, 0.9, 0.95, 0.99],
        'KNN__n_neighbors': [1, 3, 5, 10],
        'KNN__weights': ['uniform', 'distance'],
        'KNN__metric': ['euclidean', 'manhattan', 'cosine']
    }]

    # Define the pipe object to use in Grid Search
    pipe_knn = Pipeline([
        ('scaler', StandardScaler()),
        ('pca', PCA()),
        ('KNN', KNeighborsClassifier())
    ])

    # Create a grid search object and parameters to be searched
    knn_grid_search = GridSearchCV(
        estimator=pipe_knn,
        param_grid=knn_param_grid,
        scoring='accuracy',
        cv=cv
    )

    # Fit the data to the training data
    knn_grid_search.fit(train_embeddings, train_labels)

    # Save the best fit model to the model folder
    joblib.dump(knn_grid_search.best_estimator_, species.model_location())


def upload_annotations_to_training(annotations: List[Annotation]) -> None:
    for annotation in annotations:
        if annotation['accepted'] is False:
            continue

        species = Species.from_string(annotation['predicted_species'])
        if species is None:
            continue

        upload_path = f"{species.training_data_location()}/{annotation['predicted_name']}/{annotation['id']}.jpg"
        s3_bucket.upload_file(annotation['cropped_file_name'], upload_path)
