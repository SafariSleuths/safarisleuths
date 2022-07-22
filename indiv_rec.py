#!/usr/bin/python
import os
import glob
from PIL import Image
import torch
import torch.nn as nn
import torchvision
from torchvision import transforms
import pandas as pd
from joblib import load
from sklearn.preprocessing import normalize


def predict_individuals(path2data, embedding_model, device, classifier):
    """
    Parameters:
    path2data: the full local filepath to a folder of cropped images of individuals
    embedding_model: a pre-trained Resnet backbone to extract the feature embeddings
    device: whether to produce predictions on CPU or GPU
    classifier: a pre-trained classifier pipeline object
    Returns: a dataframe of full image paths and their predicted labels
    """
    # Create a list to store the embeddings
    embeddings = []
    embedding_model = embedding_model.to(device)
    embedding_model.eval()
    # Obtain the full file paths to each image in the folder
    img_dir = glob.glob(path2data + '/*')
    # Retrieve the original file names - these should be the JPG filenames produced by Yolov cropping
    filename = [x.split('/')[-1] for x in img_dir]
    # Set the transformation to enable model evaluation - normalize the input images using ImageNet values
    im_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    # Obtain the embedding for each image in the folder
    with torch.no_grad():
        for img in img_dir:
            im = Image.open(img).convert('RGB')
            im = im_transform(im)
            im = im.to(device)
            embedding = embedding_model(im).flatten(start_dim=1)
            embeddings.append(embedding)
    embeddings = torch.cat(embeddings, 0)
    embeddings = embeddings.cpu()
    embeddings = normalize(embeddings)
    # Convert the embeddimngs to an array and make predictoons
    test_embed = np.array(embeddings)
    predictions = classifier.predict(test_embed)
    df = pd.dataframe({'image': filename, 'predicted_labels': predictions})
    return df
