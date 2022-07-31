from __future__ import annotations

import json
from enum import Enum
from typing import Optional, List


class Species(Enum):
    HYENA = 'Crocuta_crocuta'
    LEOPARD = 'Panthera_pardus'
    GIRAFFE = 'Giraffa_tippelskirchi'

    def __str__(self) -> str:
        return self.value

    @staticmethod
    def from_string(s: str) -> Optional[Species]:
        for species in Species:
            if species.value == s:
                return species
        return None

    def training_data_location(self) -> str:
        return f'training_data/cropped/{self}'

    def model_location(self) -> str:
        return f'models/{self}_knn.joblib'

    def labels_location(self) -> str:
        return f'models/{self}_labels.json'

    def read_labels(self) -> List[str]:
        with open(self.labels_location()) as f:
            return json.load(f)
