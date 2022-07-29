## Available Scripts

### `ImagesAndAnnotations.ipynb`

Recovers the annotations fields from the corrupted hyena and leopard annotations files and stores the corrected json files.

### `add_coco_unlabeled.ipynb`

Moves the randomly selected Coco 2017 images into the YOLOv5 folder in preparation for model training.

### `all_animal_folder_creation.ipynb`

Creates training, validation, and test folders for all animals (regardless of species) to train the SimCLR model. 

### `hyena_leopard_bb_crop.ipynb`

Performs the following steps: 1) splits the hyena and leopard images into training, validation, and test, 2) removes leading zeros from the image names, 3) crops the images according to their Coco bounding boxes in their respective annotations files, and 4) saves the cropped images to their respective folders (train, validation, and test) for individual recognition. 

### `random_background_choices.ipynb`

Randomly selects a number of unlabeled images from the downloaded Coco2017 unlabeled dataset and moves the randomly selected images into a new folder.

### `resize_img_coco2yolo.ipynb`

This notebook creates the training, validation, and test data that is used to train and evaluate YOLOV5 from our species datasets and annotations. In this notebook, we perform the following steps: 1) resize all training, validation, and test images for all species to the input size needed for YOLOv5 (640x640), 2) converts the image bounding boxes from their original Coco format to txt files in YOLO format for model training (one txt file per image), 3) save these resized images and txt label files to their respective training, validation, and test subfolders within the image and labels subfolders in the customdata directory that we created in the cloned Ultralytics YOLOv5 repo.

### `zebra_giraffe_id.ipynb`

This notebook filters the zebra and giraffe dataset for giraffe images and splits the giraffe images into training, validation, and test, ensuring that images for animals only observed once are incorporated into the training images rather than validation or test. In addition to performing the data image split, this notebook is also used to perform the following steps: 1) remove leading zeros from the image names, 2) crop the images according to their Coco bounding boxes in their respective annotations files, and 3) save the cropped images to their respective folders (train, validation, and test) for individual recognition.
