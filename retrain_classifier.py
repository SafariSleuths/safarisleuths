import logging
import tempfile
from typing import List, NamedTuple, Tuple

import numpy as np
import torch
from PIL import Image
from joblib import dump
from sklearn.decomposition import PCA
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import normalize
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

from api.annotations import Annotation
from api.s3_client import s3_bucket
from api.species import Species
from predict_individual import load_backbone

logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(pathname)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d:%H:%M:%S'
)

logger = logging.getLogger(__name__)


class TrainInput(NamedTuple):
    file_name: str
    species: str
    name: str


class TrainDataset(Dataset):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    def __init__(self, species: Species):
        self.inputs = []
        for obj in s3_bucket.objects.filter(Prefix=species.training_data_location()):
            if obj.key.endswith('.jpg'):
                self.inputs.append(TrainInput(
                    file_name=obj.key,
                    species=species.value,
                    name=obj.key.split('/')[-2]
                ))

        self.labels = list({x.name for x in self.inputs})
        self.labels.sort()

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        obj = s3_bucket.Object(self.inputs[idx].file_name)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.jpg') as f:
            obj.download_fileobj(f)
            f.flush()
            f.seek(0)
            image = Image.open(f).convert('RGB')
        image = self.transform(image)
        return image, self.labels.index(self.inputs[idx].name)


def generate_embeddings(backbone, data_loader: DataLoader) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parameters:
    embedding_model: a pretrained Resnet 18 backbone
    data_loader: a dataloader object for which to return embeddings and labels
    Returns: a numpy array of embeddings and labels
    """

    embeddings = []
    labels = []

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = backbone.to(device)
    model.eval()
    with torch.no_grad():
        for im, label in data_loader:
            im = im.to(device)
            embed = model(im).flatten(start_dim=1)
            embeddings.append(embed)
            labels.append(label)
    embeddings = torch.cat(embeddings, 0).cpu()
    embeddings = normalize(embeddings)
    return np.array(embeddings), np.array(labels)


def retrain_classifier(new_annotations: List[Annotation]) -> None:
    if len(new_annotations) == 0:
        return

    retrain_species = set()
    for annotation in new_annotations:
        if annotation['ignored'] is True or annotation['accepted'] is False:
            continue

        species = Species.from_string(annotation['predicted_species'])
        if species is not None:
            upload_path = f"{species.training_data_location()}/{annotation['predicted_name']}/{annotation['id']}.jpg"
            s3_bucket.upload_file(annotation['cropped_file_name'], upload_path)
            retrain_species.add(species)
        else:
            logger.info(f"Skipping annotation for species `{annotation['predicted_species']}`.")

    backbone, device = load_backbone()
    for species in retrain_species:
        logger.info(f'Retraining of {species} classifier started.')
        full_classifier_retrain(backbone, species)
        logger.info(f'Retraining of {species} classifier completed. Model saved as {species.model_location()}.')


def full_classifier_retrain(backbone, species: Species) -> None:
    train_ds = TrainDataset(species)
    # Create a data loader object, but set the batch size to be 1 so that no training examples are dropped
    train_dl = DataLoader(train_ds, batch_size=1, shuffle=True, num_workers=2, drop_last=True)

    # Obtain the training data embeddings
    train_output = generate_embeddings(backbone, train_dl)
    train_embeddings = train_output[0]
    train_labels = train_output[1]

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
    dump(knn_grid_search.best_estimator_, species.model_location())
