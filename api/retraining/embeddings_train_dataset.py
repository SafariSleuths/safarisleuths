import glob
import random
from typing import NamedTuple, List

from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import transforms

from api.data_models.annotations import Annotation


class TrainInput(NamedTuple):
    file_name: str
    name: str


class EmbeddingsTrainDataset(Dataset):
    transform = transforms.Resize((224, 224))

    def __init__(self, new_annotations: List[Annotation], num2sample: int):
        self.inputs = []

        for file_name in glob.glob(f'training_data/cropped/*/*/*.jpg'):
            self.inputs.append(TrainInput(
                file_name=file_name,
                name=file_name.split('/')[-2]
            ))
        self.inputs = random.sample(self.inputs, num2sample)

        for annotation in new_annotations:
            self.inputs.append(TrainInput(
                file_name=annotation['cropped_file_name'],
                name=annotation['predicted_name']
            ))

        self.labels = list({x.name for x in self.inputs})
        self.labels.sort()

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, idx):
        label = self.labels.index(self.inputs[idx].name)
        file_name = self.inputs[idx].file_name
        image = Image.open(file_name)
        image = self.transform(image)
        return image, label, file_name
