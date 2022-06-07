import os.path
from typing import Tuple, List

import requests

from api.server import SessionResponse, PredictionResponse, ImagePredictions, AnimalSummary, ListFilesResponse, \
    UploadFilesResponse, DeleteFilesResponse, DeleteFilesRequest, PredictionRequest

ENDPOINT = 'http://localhost:5000/api/v1'


class CapstoneClient:
    def __init__(self, endpoint: str = ENDPOINT, session_id: int = 0):
        self.endpoint = endpoint
        self.session_id = session_id

    def new_session(self) -> str:
        data: SessionResponse = requests.get(f'{self.endpoint}/session').json()
        self.session_id = data['session_id']
        return data['session_id']

    def list_files(self) -> List[str]:
        data: ListFilesResponse = requests.post(
            f'{self.endpoint}/list_files',
            data={'session_id': self.session_id}
        ).json()
        return data['images']

    def upload_files(self, files: List[str]) -> List[str]:
        data: UploadFilesResponse = requests.post(
            f'{self.endpoint}/list_files',
            files={os.path.basename(fname): open(fname) for fname in files},
            data={'session_id': self.session_id}
        ).json()
        return data['images']

    def delete_files(self, files: List[str]) -> List[str]:
        data: DeleteFilesResponse = requests.get(
            f'{self.endpoint}/list_files',
            data=DeleteFilesRequest(session_id=self.session_id, files=files)
        ).json()
        return data['deleted']

    def make_prediction(self) -> Tuple[List[ImagePredictions], List[AnimalSummary]]:
        data: PredictionResponse = requests.get(
            f'{self.endpoint}/predict',
            data=PredictionRequest(session_id=self.session_id)
        ).json()
        return data['results'], data['summary']
