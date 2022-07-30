from typing import NamedTuple, List
import PIL
from PIL import Image

from api.images import list_image_paths_for_collection



class InputImage(NamedTuple):
    file_name: str
    original_image: PIL.Image.Image
    original_height: int
    original_width: int
    resized_image: PIL.Image.Image


def read_images_for_collection(collection_id: str) -> List[InputImage]:
    return read_images(list_image_paths_for_collection(collection_id))


def read_images(file_names: List[str]) -> List[InputImage]:
    images = []
    for file_name in file_names:
        pil_image = PIL.Image.open(file_name)
        width, height = pil_image.size
        images.append(InputImage(
            file_name=file_name,
            original_image=pil_image,
            original_height=height,
            original_width=width,
            resized_image=pil_image.resize((640, 640))
        ))
    return images
