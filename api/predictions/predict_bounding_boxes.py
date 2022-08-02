import logging
import os.path
from datetime import datetime
from typing import NamedTuple, Optional, List, Tuple

import PIL
import torch
from PIL import Image, ImageDraw

from api.data_models.prediction_inputs import InputImage, read_images_for_collection
from api.clients.s3_client import s3_bucket

logger = logging.getLogger(__name__)

OUTPUTS_PATH = 'website-data/outputs'
BOX_COLOR = (0, 0, 255)


class BoundingBox(NamedTuple):
    x: float
    y: float
    w: float
    h: float

    def to_xy(self) -> Tuple[int, int, int, int]:
        return int(self.x), int(self.y), int(self.x + self.w), int(self.y + self.h)


class YolovPrediction(NamedTuple):
    file_name: str
    id: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    bbox: Optional[BoundingBox]
    confidence: Optional[float]
    predicted_species: Optional[str]


def predict_bounding_boxes_for_collection(collection_id: str) -> List[YolovPrediction]:
    logger.info("Started bounding box prediction.")
    start_time = datetime.now()

    model = torch.hub.load(
        'ultralytics/yolov5', 'custom', 'models/frozen_backbone_coco_unlabeled.pt',
        autoshape=True, force_reload=True
    )

    yolov_predictions: List[YolovPrediction] = []
    for input_image in read_images_for_collection(collection_id):
        yolov_predictions += predict_bounding_boxes(model, input_image, collection_id)
    logger.info(f'Bounding box predictions completed after {datetime.now() - start_time}.')

    logger.info(f'Uploading results.')
    start_time = datetime.now()
    for prediction in yolov_predictions:
        if prediction.predicted_species is None:
            continue
        image = PIL.Image.open(prediction.file_name)
        crop_and_upload(
            image=image.copy(),
            dest=prediction.cropped_file_name,
            bbox=prediction.bbox
        )
        annotate_and_upload(
            image=image.copy(),
            dest=prediction.annotated_file_name,
            bbox=prediction.bbox
        )
    logger.info(f'Results uploaded after {datetime.now() - start_time}.')
    return yolov_predictions


def predict_bounding_boxes(model, input_image: InputImage, collection_id: str) -> List[YolovPrediction]:
    raw_results = model(input_image.resized_image, size=640).pandas().xyxy[0]
    raw_results.reset_index()

    if len(raw_results) == 0:
        return [
            YolovPrediction(
                file_name=input_image.file_name,
                id=os.path.basename(input_image.file_name.removesuffix('.jpg')),
                annotated_file_name=None,
                cropped_file_name=None,
                bbox=None,
                confidence=None,
                predicted_species=None
            )
        ]

    predictions = []
    for idx, prediction in raw_results.iterrows():
        species_name = prediction['name']
        output_file_name = f'{idx}_{os.path.basename(input_image.file_name)}'
        predictions.append(YolovPrediction(
            id=output_file_name.removesuffix('.jpg'),
            file_name=input_image.file_name,
            annotated_file_name=f'{OUTPUTS_PATH}/{collection_id}/annotated/{species_name}/{output_file_name}',
            cropped_file_name=f'{OUTPUTS_PATH}/{collection_id}/cropped/{species_name}/{output_file_name}',
            bbox=yolov2coco(
                xmin=prediction['xmin'],
                xmax=prediction['xmax'],
                ymin=prediction['ymin'],
                ymax=prediction['ymax'],
                original_width=input_image.original_width,
                original_height=input_image.original_height
            ),
            confidence=prediction['confidence'],
            predicted_species=prediction['name']
        ))

    return predictions


def crop_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    image.crop(bbox.to_xy()).save(dest)
    if s3_bucket is not None:
        s3_bucket.upload_file(dest, dest)


def annotate_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    ImageDraw.Draw(image).rectangle(bbox.to_xy(), outline=BOX_COLOR, width=5)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    image.save(dest)
    if s3_bucket is not None:
        s3_bucket.upload_file(dest, dest)


def yolov2coco(
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        original_height: float,
        original_width: float
) -> BoundingBox:
    """
    Converts the Yolov predictions to Coco format, scaled to the input image size.
    """
    x1 = (xmin / 640) * original_width
    x2 = (xmax / 640) * original_width
    y1 = (ymin / 640) * original_height
    y2 = (ymax / 640) * original_height
    w = x2 - x1
    h = y2 - y1
    return BoundingBox(x=x1, y=y1, w=w, h=h)
