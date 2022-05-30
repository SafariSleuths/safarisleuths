import os.path
from typing import Any
import torch
import numpy as np
from torchvision.models import detection
import cv2

min_confidence = 0.75
box_color = (255, 0, 0)

model = detection.fasterrcnn_resnet50_fpn(pretrained=True)
model.eval()


def process_image(input_path: str, output_path: str) -> int:
    image = cv2.imread(input_path)
    objects = detect_objects(image.copy())
    annotated_image = draw_bounding_boxes(image, objects)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, annotated_image)
    return count_zebras(objects)


def detect_objects(image):
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = image.transpose((2, 0, 1))
    image = np.expand_dims(image, axis=0)
    image = image / 255.0
    image = torch.FloatTensor(image)
    return model(image)[0]


def count_zebras(detections) -> int:
    count = 0
    for i in range(0, len(detections["boxes"])):
        idx = int(detections["labels"][i])
        if idx == 24:  # Zebra
            count += 1
    return count


def draw_bounding_boxes(image, detections) -> Any:
    for i in range(0, len(detections["boxes"])):
        idx = int(detections["labels"][i])
        if idx != 24:  # Zebra
            continue

        confidence = detections["scores"][i]
        if min_confidence > confidence:
            continue

        box = detections["boxes"][i].detach().cpu().numpy()
        (startX, startY, endX, endY) = box.astype("int")
        label = f"zebra: {confidence * 100:.2f}%"
        cv2.rectangle(image, (startX, startY), (endX, endY), box_color, 2)
        y = startY - 15 if startY - 15 > 15 else startY + 15
        cv2.putText(image, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)
    return image
