from __future__ import annotations

from enum import Enum
from typing import Optional


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
        if self == Species.HYENA:
            return 'hyena.coco/processed/train/'
        elif self == Species.LEOPARD:
            return 'leopard.coco/processed/train/'
        elif self == Species.GIRAFFE:
            return 'great_zebra_giraffe/individual_recognition/train/'

    def model_location(self) -> str:
        if self == Species.HYENA:
            return 'models/hyena_knn_last.joblib'
        elif self == Species.LEOPARD:
            return 'models/leopard_knn_last.joblib'
        elif self == Species.GIRAFFE:
            return 'models/giraffe_knn_last.joblib'
