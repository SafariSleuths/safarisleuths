import os
from typing import NamedTuple, List
import PIL
from PIL import Image
from werkzeug.datastructures import ImmutableMultiDict, FileStorage

from api.s3_client import s3_bucket

INPUTS_PATH = 'website-data/inputs'


class InputImage(NamedTuple):
    file_name: str
    original_image: PIL.Image.Image
    original_height: int
    original_width: int
    resized_image: PIL.Image.Image


def save_images_for_session(session_id: str, files: ImmutableMultiDict[str, FileStorage]) -> None:
    os.makedirs(f'{INPUTS_PATH}/{session_id}', exist_ok=True)
    uploaded = []
    for file_name in files:
        dest = f'{INPUTS_PATH}/{session_id}/{os.path.basename(file_name)}'
        files[file_name].save(dest)
        s3_bucket.upload_file(dest, dest)
        uploaded.append(dest)


def read_images_for_session(session_id: str) -> List[InputImage]:
    return read_images(image_paths_for_session(session_id))


def image_paths_for_session(session_id: str) -> List[str]:
    return [o.key for o in s3_bucket.objects.filter(Prefix=f'{INPUTS_PATH}/{session_id}/')]


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
