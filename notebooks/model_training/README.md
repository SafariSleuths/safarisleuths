## Available Scripts

### `Yolov5_frozen_backbone_unlabeled.ipynb`

The code to finetune a Yolov5 model for custom class prediction, using a batch size of 32, an input image size of 640, and training for 100 epochs. To run this script, you will need to have already performed the following steps: cloned https://github.com/ultralytics/yolov5, created a custom class yaml file in the data folder of the cloned yolov5 repo, created a directory called custom_data with subdirectories for images and labels in the cloned Yolov5 folder, created train, validation, and test subfolders within the image and labels subfolders, and added your images (size 640x640) and txt label files to the train, validation, and test subfolders. In the training image folder, you should also have added your unlabeled images (also size 640x640), which should account for 10 - 15% of the total number of training images. 

Creates the Yolov5 onxx model `frozen_backbone_coco_unlabeled_best.pt`.

### `batch320_simclr_lightly.ipynb`

Creates and trains a SimCLR model with a ResNet18 backbone and a batch size of 320 images, for 180 epochs, or until the validation loss stops improving for 5 steps. Saves the model backbone for future feature extraction and retraining (`simclrresnet18embed.pth`), as well as the trained projection head (`simclr_projectionhead.pth`).

### `giraffe_classifier_bs320.ipynb`

Trains and fits a KNN classifier pipeline on the Giraffa tippelskirchi training dataset (`Giraffa_tippelskirchi_knn.joblib`), as well as a lookup map to convert the integer labels produced by the model back to string ids. 

### `hyena_classifier_bs320.ipynb`

Trains and fits a KNN classifier pipeline on the Crocuta crocuta training dataset (`Crocuta_crocuta_knn.joblib`), as well as a lookup map to convert the integer labels produced by the model back to string ids.

### `leopard_classifier_bs320.ipynb`

Trains and fits a KNN classifier pipeline on the Panthera pardus training dataset (`Panthera_pardus_knn.joblib`), as well as a lookup map to convert the integer labels produced by the model back to string ids.
