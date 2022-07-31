import json
import logging
from datetime import datetime
from typing import NamedTuple, List, Dict, Iterable, Optional, Tuple

import numpy as np
import torch
import torchvision
import PIL.Image
import joblib
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from sklearn.preprocessing import normalize

from api.data_models.species import Species
from api.predictions.predict_bounding_boxes import YolovPrediction

logger = logging.getLogger(__name__)

BACKBONE_PATH = 'models/simclrresnet18embed.pth'


class LocalImageDataset(Dataset):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    def __init__(self, file_names: List[str]):
        self.file_names = file_names

    def __len__(self):
        return len(self.file_names)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        file_name = self.file_names[idx]
        image = PIL.Image.open(file_name).convert('RGB')
        return self.transform(image), 0


class NoneClassifier:
    @staticmethod
    def predict(embeddings) -> Iterable[None]:
        return [None] * len(embeddings)


class IndividualPrediction(NamedTuple):
    cropped_file_name: str
    individual_label: Optional[int]
    individual_name: Optional[str]


def predict_individuals_from_yolov_predictions(yolov_predictions: List[YolovPrediction]) -> List[IndividualPrediction]:
    logger.info(f'Starting individual prediction for {len(yolov_predictions)} images.')
    start_time = datetime.now()
    backbone, device = load_backbone()
    results = []
    for species, yolov_predictions in group_yolov_predictions_by_species(yolov_predictions).items():
        results += predict_individuals_from_species(
            backbone=backbone,
            device=device,
            species=species,
            file_names=[p.cropped_file_name for p in yolov_predictions]
        )
    logger.info(f'Individual predictions completed after {datetime.now() - start_time}.')

    return results


def load_backbone():
    resnet18 = torchvision.models.resnet18()
    backbone = torch.nn.Sequential(*list(resnet18.children())[:-1])
    ckpt = torch.load(BACKBONE_PATH)
    backbone.load_state_dict(ckpt['resnet18_parameters'])
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    backbone = backbone.to(device)
    backbone.eval()
    return backbone, device


def group_yolov_predictions_by_species(
        predictions: List[YolovPrediction]
) -> Dict[Optional[Species], List[YolovPrediction]]:
    results = {}
    for prediction in predictions:
        # If this species is not something we know about or None, this returns a None value.
        species = Species.from_string(prediction.predicted_species or '')
        if species not in results:
            results[species] = []
        results[species].append(prediction)
    return results


def predict_individuals_from_species(
        backbone,
        device,
        species: Optional[Species],
        file_names: List[str]
) -> List[IndividualPrediction]:
    if species is None:
        return [
            IndividualPrediction(
                cropped_file_name=file_name,
                individual_label=None,
                individual_name=None
            )
            for file_name in file_names
        ]

    classifier = joblib.load(species.model_location())
    with open(species.labels_location()) as f:
        labels = json.load(f)

    embeddings = images_to_embeddings(backbone, device, file_names)
    predicted_labels = classifier.predict(embeddings)
    results = []
    for file_name, label_idx in zip(file_names, predicted_labels):
        results.append(IndividualPrediction(
            cropped_file_name=file_name,
            individual_label=label_idx,
            individual_name=labels[label_idx]
        ))

    return results


def images_to_embeddings(backbone, device, file_names: List[str]) -> np.ndarray:
    embedding_tensors = []

    data_loader = DataLoader(LocalImageDataset(file_names), batch_size=1, shuffle=False)
    with torch.no_grad():
        for batch, _ in data_loader:
            embedding = backbone(batch.to(device)).flatten(start_dim=1)
            embedding_tensors.append(embedding)

    embeddings = normalize(torch.cat(embedding_tensors, 0).cpu())
    return np.array(embeddings)
