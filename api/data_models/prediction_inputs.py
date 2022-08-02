import glob
import os
from typing import NamedTuple, List
import PIL
from PIL import Image

from werkzeug.datastructures import ImmutableMultiDict, FileStorage

from api.clients.s3_client import s3_bucket

INPUTS_PATH = 'website-data/inputs'


class InputImage(NamedTuple):
    file_name: str
    original_image: PIL.Image.Image
    original_height: int
    original_width: int
    resized_image: PIL.Image.Image


def list_image_paths_for_collection(collection_id: str) -> List[str]:
    if s3_bucket is not None:
        return [o.key for o in s3_bucket.objects.filter(Prefix=f'{INPUTS_PATH}/{collection_id}/')]
    return [fname for fname in glob.glob(f'{INPUTS_PATH}/{collection_id}/**.jpg')]


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


def save_images_for_collection(collection_id: str, files: ImmutableMultiDict[str, FileStorage]) -> List[str]:
    os.makedirs(f'{INPUTS_PATH}/{collection_id}', exist_ok=True)
    uploaded = []
    for file_name in files:
        dest = f'{INPUTS_PATH}/{collection_id}/{os.path.basename(file_name)}'
        files[file_name].save(dest)
        if s3_bucket is not None:
            s3_bucket.upload_file(dest, dest)
        uploaded.append(dest)
    return uploaded


def delete_images_for_collection(collection_id: str, file_names: List[str]) -> None:
    real_file_names = []
    for file_name in file_names:
        real_file_names.append(f'{INPUTS_PATH}/{collection_id}/{os.path.basename(file_name)}')

    for file_name in real_file_names:
        try:
            os.remove(file_name)
        except FileNotFoundError:
            pass

    s3_bucket.delete_objects(Delete={'Objects': [{'Key': key} for key in real_file_names]})
