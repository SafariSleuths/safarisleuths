import json
import time
from datetime import datetime
from logging import Logger
from multiprocessing import Process
from typing import List, Tuple, Dict

import numpy as np
import torch
import joblib
from flask import Blueprint
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import normalize
from torch.utils.data import DataLoader

from api import retrain_job
from api.annotations import Annotation, read_annotations_for_collection
from api.local_train_dataset import LocalTrainDataset
from api.retrain_job import RetrainStatus, log_event, RetrainEventLog, truncate_job_logs
from api.s3_client import s3_bucket
from api.collections import must_get_collection_id
from api.species import Species
from api.predict_individual import load_backbone
from api.status_response import StatusResponse
from flask import current_app

flask_blueprint = Blueprint('retrain_classifier', __name__)


@flask_blueprint.post('/api/v1/retrain/start')
def post_retrain() -> StatusResponse:
    collection_id = must_get_collection_id()

    retrain_job.save_job_status_to_redis(RetrainStatus(
        collection_id=collection_id,
        created_at=time.time(),
        status='created'
    ))
    Process(target=retrain_classifier, args=(collection_id, current_app.logger)).start()
    return {'status': 'ok'}


def retrain_classifier(collection_id: str, logger: Logger) -> None:
    def __log_event(message: str) -> None:
        logger.info(message)
        log_event(RetrainEventLog(collection_id=collection_id, created_at=time.time(), message=message))

    def __should_abort() -> bool:
        job = retrain_job.read_job_status_from_redis(collection_id)
        if job['status'] == 'aborted':
            __log_event('Retraining aborted!')
            return True
        return False

    truncate_job_logs(collection_id)
    __log_event(f'Started retraining for collection {collection_id}.')

    job = retrain_job.read_job_status_from_redis(collection_id)
    job['status'] = 'started'
    retrain_job.save_job_status_to_redis(job)

    new_annotations = read_annotations_for_collection(collection_id)
    new_annotations = [a for a in new_annotations if a['accepted']]
    if len(new_annotations) == 0:
        job['status'] = 'completed'
        retrain_job.save_job_status_to_redis(job)
        __log_event('Retraining skipped since there are no new annotations for training.')
        return

    __log_event(f"Retraining with {len(new_annotations)} new annotation{'s' if len(new_annotations) != 1 else ''}.")

    backbone, device = load_backbone()

    grouped_annotations = __group_annotations_by_species(new_annotations)
    for species in grouped_annotations.keys():
        __log_event(f'Found new training data for the {species} classifier.')

    for species, annotations in grouped_annotations.items():
        if __should_abort():
            return

        __log_event(f'Loading training data for the {species} classifier.')
        load_data_start_time = datetime.now()
        train_dataset = LocalTrainDataset(species, new_annotations)
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=1,  # Batch size to be 1 so that no training examples are dropped.
            shuffle=True,
            num_workers=2,
            drop_last=True
        )
        train_embeddings, train_labels = generate_embeddings(backbone, train_dataloader)
        __log_event(
            f'Loaded {len(train_embeddings)} embeddings for {species} after {datetime.now() - load_data_start_time}.')

        if __should_abort():
            return
        __log_event(f'Started retraining for the {species} classifier.')
        retrain_start_time = datetime.now()
        retrain_classifier_for_species(
            species=species,
            train_embeddings=train_embeddings,
            train_labels=train_labels
        )
        __log_event(f'Completed retraining for the {species} classifier after {datetime.now() - retrain_start_time}.')
        logger.info(f'Model saved as {species.model_location()}')

        with open(species.labels_location(), 'w') as f:
            json.dump(train_dataset.labels, f)

    job['status'] = 'completed'
    retrain_job.save_job_status_to_redis(job)
    __log_event(f'Completed all retraining tasks for collection {collection_id}.')


def __group_annotations_by_species(annotations: List[Annotation]) -> Dict[Species, List[Annotation]]:
    results = {}
    for annotation in annotations:
        species = Species.from_string(annotation['predicted_species'])
        if species not in results:
            results[species] = []

        results[species].append(annotation)
    return results


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


def retrain_classifier_for_species(
        species: Species,
        train_embeddings: np.ndarray,
        train_labels: np.ndarray,
) -> None:
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
