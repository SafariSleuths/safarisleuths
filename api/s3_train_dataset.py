import tempfile
from typing import List, NamedTuple, Tuple

import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from api.annotations import Annotation
from api.s3_client import s3_bucket
from api.species import Species


class TrainInput(NamedTuple):
    file_name: str
    name: str


class S3TrainDataset(Dataset):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    def __init__(self, species: Species, new_annotations: List[Annotation]):
        self.inputs = []
        for obj in s3_bucket.objects.filter(Prefix=species.training_data_location()):
            if obj.key.endswith('.jpg'):
                self.inputs.append(TrainInput(
                    file_name=obj.key,
                    name=obj.key.split('/')[-2]
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
        obj = s3_bucket.Object(self.inputs[idx].file_name)
        with tempfile.NamedTemporaryFile(mode='wb+', suffix='.jpg') as f:
            obj.download_fileobj(f)
            f.flush()
            f.seek(0)
            image = Image.open(f).convert('RGB')
        image = self.transform(image)
        return image, self.labels.index(self.inputs[idx].name)
