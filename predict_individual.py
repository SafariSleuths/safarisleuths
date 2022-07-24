import json
from typing import NamedTuple, List, Dict, Iterable, Optional, Tuple

import numpy as np
import torch
import torchvision
import PIL.Image
import joblib
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from sklearn.preprocessing import normalize

from predict_bounding_boxes import YolovPrediction

MODELS_PATH = 'individ_rec_modelsandhelpers'


class IndividualPrediction(NamedTuple):
    cropped_file_name: str
    individual_label: Optional[int]
    individual_name: Optional[str]


def group_yolov_predictions_by_species(predictions: List[YolovPrediction]) -> Dict[str, List[YolovPrediction]]:
    results = {}
    for prediction in predictions:
        species = prediction.predicted_species
        if species not in results:
            results[species] = []
        results[species].append(prediction)
    return results


def predict_individuals_from_yolov_predictions(yolov_predictions: List[YolovPrediction]) -> List[IndividualPrediction]:
    # Load the pre-trained embeddings from the previously trained model backbone
    resnet18_new = torchvision.models.resnet18()

    ckpt = torch.load('individ_rec_modelsandhelpers/simclrresnet18embed.pth')
    backbone_new = torch.nn.Sequential(*list(resnet18_new.children())[:-1])
    backbone_new.load_state_dict(ckpt['resnet18_parameters'])

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    backbone_new = backbone_new.to(device)
    backbone_new.eval()

    results = []
    for species, yolov_predictions in group_yolov_predictions_by_species(yolov_predictions).items():
        results += predict_individuals_from_species(
            backbone=backbone_new,
            device=device,
            species=species,
            file_names=[p.cropped_file_name for p in yolov_predictions]
        )

    return results


class NoneClassifier:
    @staticmethod
    def predict(embeddings) -> Iterable[None]:
        return [None] * len(embeddings)


def predict_individuals_from_species(
        backbone,
        device,
        species: str,
        file_names: List[str]
) -> List[IndividualPrediction]:
    classifier = NoneClassifier
    label_to_name = {None: None}

    if species == 'Crocuta_crocuta':
        classifier = joblib.load(f'{MODELS_PATH}/hyena_knn.joblib')
        label_to_name = joblib.load(f'{MODELS_PATH}/hyena_id_map.joblib')

    if species == 'Panthera_pardus':
        classifier = joblib.load(f'{MODELS_PATH}/leopard_knn.joblib')
        label_to_name = joblib.load(f'{MODELS_PATH}/leopard_id_map.joblib')

    if species == 'Giraffa_tippelskirchi':
        classifier = joblib.load(f'{MODELS_PATH}/giraffe_knn.joblib')
        label_to_name = joblib.load(f'{MODELS_PATH}/giraffe_id_map.joblib')

    embeddings = images_to_embeddings(backbone, device, file_names)
    predicted_labels = classifier.predict(embeddings)
    results = []
    for file_name, label in zip(file_names, predicted_labels):
        results.append(IndividualPrediction(
            cropped_file_name=file_name,
            individual_label=label,
            individual_name=label_to_name.get(label))
        )

    return results


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


def images_to_embeddings(backbone, device, file_names: List[str]) -> np.ndarray:
    embedding_tensors = []

    data_loader = DataLoader(LocalImageDataset(file_names), batch_size=1)
    with torch.no_grad():
        for batch, _ in data_loader:
            embedding = backbone(batch.to(device)).flatten(start_dim=1)
            embedding_tensors.append(embedding)

    embeddings = normalize(torch.cat(embedding_tensors, 0).cpu())
    return np.array(embeddings)
