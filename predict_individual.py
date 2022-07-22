from typing import NamedTuple, List, Dict, Iterable, Optional

import numpy as np
import torch
import torchvision
import PIL.Image
from joblib import load
from torchvision import transforms
from sklearn.preprocessing import normalize

from predict_bounding_boxes import YolovPrediction


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

    ckpt = torch.load('resnet18embed.pth')
    backbone_new = torch.nn.Sequential(*list(resnet18_new.children())[:-1])
    backbone_new.load_state_dict(ckpt['resnet18_parameters'])

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    backbone_new = backbone_new.to(device)
    backbone_new.eval()

    results = []
    for species, yolov_predictions in group_yolov_predictions_by_species(yolov_predictions):
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
        classifier = load('hyena_knn.joblib')
        label_to_name = load('hyena_id_map.joblib')

    if species == 'Panthera_pardus':
        classifier = load('leopard_knn.joblib')
        label_to_name = load('leopard_id_map.joblib')

    if species == 'Giraffa_tippelskirchi':
        classifier = load('giraffe_knn.joblib')
        label_to_name = load('giraffe_id_map.joblib')

    images = [PIL.Image.open(file_name).convert('RGB') for file_name in file_names]
    embeddings = images_to_embeddings(backbone, device, images)
    predicted_labels = classifier.predict(embeddings)
    results = []
    for file_name, label in zip(file_names, predicted_labels):
        results.append(IndividualPrediction(
            cropped_file_name=file_name,
            individual_label=label,
            individual_name=label_to_name.get(label))
        )

    return results


def images_to_embeddings(backbone, device, images: List[PIL.Image.Image]) -> np.ndarray:
    im_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        # Normalize the input images using ImageNet values.
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    embedding_tensors = []
    with torch.no_grad():
        for im in images:
            im = im_transform(im)
            im = im.to(device)
            embedding = backbone(im).flatten(start_dim=1)
            embedding_tensors.append(embedding)

    embeddings = normalize(torch.cat(embedding_tensors, 0).cpu())
    return np.array(embeddings)
