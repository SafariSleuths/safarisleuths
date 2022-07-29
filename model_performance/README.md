## Available Scripts

### `individual_recognition_mistakes.ipynb`

Evaluates the performance of the species specific KNN classifiers for individual recognition on the test datasets and finds the top-1 accuracy scores, weighted precision, and weighted recall on these images. Includes additional analysis of model mistakes, as measured by number of training appearances.

### `yolo_test_preds&analysis.ipynb`

Evaluates our YOLOv5 model fine-tuned for custom class prediction on the test dataset, as measured by accuracy, precision, recall, and f1-scores by species. Also finds the number of images that failed to be classified, and the confidence scores for image predictions. 