import glob
from typing import List, NamedTuple, Tuple

import PIL
import PIL.Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

from api.data_models.annotations import Annotation
from api.data_models.species import Species


class TrainInput(NamedTuple):
    file_name: str
    name: str


class ClassifierTrainDataset(Dataset):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    def __init__(self, species: Species, new_annotations: List[Annotation]):
        self.inputs = []

        for file_name in glob.glob(f'{species.training_data_location()}/*/*.jpg'):
            self.inputs.append(TrainInput(
                file_name=file_name,
                name=file_name.split('/')[-2]
            ))

        for annotation in new_annotations:
            self.inputs.append(TrainInput(
                file_name=annotation['cropped_file_name'],
                name=annotation['predicted_name']
            ))

        self.labels = list({x.name for x in self.inputs})
        self.labels.sort()

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx) -> Tuple[torch.Tensor, int]:
        image = PIL.Image.open(self.inputs[idx].file_name).convert('RGB')
        image = self.transform(image)
        return image, self.labels.index(self.inputs[idx].name)
