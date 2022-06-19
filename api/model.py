import os.path
import zlib
from typing import Any, Tuple, List, TypedDict
import torch
import numpy as np
from torchvision.models import detection
import cv2

RESNET_LABEL_ZEBRA = 24

MIN_CONFIDENCE = 0.75
BOX_COLOR = (255, 0, 0)  # Blue

model = detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.eval()


class BoundingBox(TypedDict):
    start: Tuple[int, int]
    end: Tuple[int, int]
    confidence: float
    label: str
    species: str
    animal_id: int


def process_image(input_path: str, output_path: str) -> List[BoundingBox]:
    image = cv2.imread(input_path)
    predictions = predict_objects(image.copy())
    boxes = prediction_to_boxes(predictions)
    annotated_image = draw_bounding_boxes(image, boxes)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated_image)
    return boxes


def predict_objects(image: Any) -> Any:
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image / 255.0
    image = torch.FloatTensor(image)
    return model(image)[0]


def prediction_to_boxes(detections: Any) -> List[BoundingBox]:
    boxes: List[BoundingBox] = []
    for i in range(0, len(detections["boxes"])):
        idx = int(detections["labels"][i])
        if idx != RESNET_LABEL_ZEBRA:
            continue

        confidence = detections["scores"][i]
        if MIN_CONFIDENCE > confidence:
            continue

        box = detections["boxes"][i].detach().cpu().numpy()
        (startX, startY, endX, endY) = box.astype("int")
        boxes.append(BoundingBox(
            start=(int(startX), int(startY)),
            end=(int(endX), int(endY)),
            confidence=float(confidence),
            label='zebra',
            species='zebra',
            # TODO: Compute a real animal id based on the animal's features.
            # CRC hash function returns a unique id for each set of coordinates.
            animal_id=zlib.crc32(f'({startX},{startY})({endX},{endY})'.encode())
        ))
    return boxes


def draw_bounding_boxes(image: Any, boxes: List[BoundingBox]) -> Any:
    for box in boxes:
        label = f"{box['label']}: {box['confidence'] * 100:.2f}%"
        cv2.rectangle(image, box['start'], box['end'], BOX_COLOR, 2)
        (text_x, text_y) = box['start']
        if text_y > 15:
            text_y -= 15
        else:
            text_y += 15
        cv2.putText(image, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, BOX_COLOR, 2)
    return image
