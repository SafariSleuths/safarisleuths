import os.path
from typing import NamedTuple, Optional, List, Tuple

import PIL
import torch
from PIL import Image, ImageDraw

from api.inputs import InputImage
from api.s3_client import s3_bucket

OUTPUTS_PATH = 'website-data/outputs'
BOX_COLOR = (0, 0, 255)

object_detection_model = torch.hub.load(
    'ultralytics/yolov5', 'custom', 'frozen_backbone_coco_unlabeled_best.onnx', autoshape=True, force_reload=True
)


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
    bbox_confidence: Optional[float]
    bbox_label: Optional[int]
    predicted_species: Optional[str]


def predict_bounding_boxes(input_image: InputImage, session_id: str) -> List[YolovPrediction]:
    raw_results = object_detection_model(input_image.resized_image, size=640).pandas().xyxy[0]
    raw_results.reset_index()

    if len(raw_results) == 0:
        return [
            YolovPrediction(
                file_name=input_image.file_name,
                id=os.path.basename(input_image.file_name.removesuffix('.jpg')),
                annotated_file_name=None,
                cropped_file_name=None,
                bbox=None,
                bbox_confidence=None,
                bbox_label=None,
                predicted_species=None
            )
        ]

    predictions = []
    for idx, prediction in raw_results.iterrows():
        species_name = prediction['name']
        output_file_name = f'{idx}_{os.path.basename(input_image.file_name)}'
        annotated_file_name = f'{OUTPUTS_PATH}/{session_id}/annotated/{species_name}/{output_file_name}'
        cropped_file_name = f'{OUTPUTS_PATH}/{session_id}/cropped/{species_name}/{output_file_name}'
        bbox = yolov2coco(
            xmin=prediction['xmin'],
            xmax=prediction['xmax'],
            ymin=prediction['ymin'],
            ymax=prediction['ymax'],
            original_width=input_image.original_width,
            original_height=input_image.original_height
        )
        crop_and_upload(
            image=input_image.original_image.copy(),
            dest=cropped_file_name,
            bbox=bbox
        )
        annotate_and_upload(
            image=input_image.original_image.copy(),
            dest=annotated_file_name,
            bbox=bbox
        )
        predictions.append(YolovPrediction(
            id=output_file_name.removesuffix('.jpg'),
            file_name=input_image.file_name,
            annotated_file_name=annotated_file_name,
            cropped_file_name=cropped_file_name,
            bbox=bbox,
            bbox_confidence=prediction['confidence'],
            bbox_label=prediction['class'],
            predicted_species=prediction['name']
        ))

    return predictions


def crop_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    image.crop(bbox.to_xy()).save(dest)
    s3_bucket.upload_file(dest, dest)


def annotate_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    ImageDraw.Draw(image).rectangle(bbox.to_xy(), outline=BOX_COLOR, width=5)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    image.save(dest)
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
