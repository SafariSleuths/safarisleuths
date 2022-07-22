from typing import NamedTuple, Optional, List, Dict, Tuple

import PIL
import torch
from PIL import Image, ImageDraw

from s3_client import s3_bucket

OUTPUTS_PATH = 'website-data/outputs'

object_detection_model = torch.hub.load(
    'ultralytics/yolov5', 'custom', 'frozen_backbone_coco_unlabeled_best.onnx', autoshape=True, force_reload=True
)


class InputImage(NamedTuple):
    file_name: str
    original_image: PIL.Image.Image
    original_height: int
    original_width: int
    resized_image: PIL.Image.Image


class BoundingBox(NamedTuple):
    x: float
    y: float
    w: float
    h: float

    def to_xy(self) -> Tuple[int, int, int, int]:
        return int(self.x), int(self.y), int(self.x + self.w), int(self.y + self.h)


class YolovPrediction(NamedTuple):
    file_name: str
    annotated_file_name: Optional[str]
    cropped_file_name: Optional[str]
    original_image: PIL.Image.Image
    bbox: Optional[BoundingBox]
    bbox_confidence: Optional[float]
    bbox_label: Optional[int]
    predicted_species: Optional[str]


def read_images(file_names: List[str]) -> List[InputImage]:
    images = []
    for file_name in file_names:
        pil_image = PIL.Image.open(file_name)
        width, height = pil_image.size
        images.append(InputImage(
            file_name=file_name,
            original_image=pil_image,
            original_height=width,
            original_width=height,
            resized_image=pil_image.resize((640, 640))
        ))
    return images


def predict_bounding_boxes(input_image: InputImage, session_id: str) -> List[YolovPrediction]:
    raw_results = object_detection_model(input_image.resized_image, size=640).pandas().xyxy[0]
    raw_results.reset_index()

    if len(raw_results) == 0:
        return [
            YolovPrediction(
                file_name=input_image.file_name,
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
        predictions.append(YolovPrediction(
            file_name=input_image.file_name,
            annotated_file_name=f'{OUTPUTS_PATH}/{session_id}/annotated/{species_name}/{idx}_{input_image.file_name}',
            cropped_file_name=f'{OUTPUTS_PATH}/{session_id}/cropped/{species_name}/{idx}_{input_image.file_name}',
            original_image=input_image.original_image,
            bbox=yolov2coco(
                xmin=prediction['xmin'],
                xmax=prediction['xmax'],
                ymin=prediction['ymin'],
                ymax=prediction['ymax'],
                original_width=input_image.original_width,
                original_height=input_image.original_height
            ),
            bbox_confidence=prediction['confidence'],
            bbox_label=prediction['class'],
            predicted_species=prediction['name']
        ))

    for prediction in predictions:
        crop_and_upload(
            image=prediction.original_image.copy(),
            dest=prediction.cropped_file_name,
            bbox=prediction.bbox
        )
        annotate_and_upload(
            image=prediction.original_image.copy(),
            dest=prediction.annotated_file_name,
            bbox=prediction.bbox
        )

    return predictions


def crop_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    image.crop(bbox.to_xy()).save(dest)
    s3_bucket.copy(dest, dest)


def annotate_and_upload(image: PIL.Image.Image, dest: str, bbox: BoundingBox) -> None:
    ImageDraw.Draw(image).rectangle(bbox.to_xy())
    image.save(dest)
    s3_bucket.copy(dest, dest)


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
    return BoundingBox(x=x1, y=y1, w=x2 - x1, h=y2 - y1)
