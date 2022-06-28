from __future__ import print_function
from __future__ import division
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import torchvision
from torchvision import datasets, models, transforms
import matplotlib.pyplot as plt
import time
import os
import copy
from datetime import datetime

print("PyTorch Version: ", torch.__version__)
print("Torchvision Version: ", torchvision.__version__)

model_name = "resnet"
num_classes = 2
batch_size = 8
num_epochs = 15
feature_extract = False


def train_model(model, trainDataLoader, evalDataLoader, criterion, optimizer, num_epochs=25):
    start_time = datetime.now()

    best_weights = copy.deepcopy(model.state_dict())
    best_accuracy = 0.0
    epoch_accuracies = []

    for epoch in range(num_epochs):
        print(f'Epoch {epoch}/{num_epochs - 1}')
        print('-' * 10)

        model.train()
        training_accuracy, training_loss = training_step(model, trainDataLoader, criterion, optimizer, False)
        print(f'Train Loss: {training_loss:.4f} Accuracy: {training_accuracy:.4f}')

        model.eval()
        epoch_acc, epoch_loss = training_step(model, evalDataLoader, criterion, optimizer, True)
        print(f'Eval Loss: {epoch_loss:.4f} Accuracy: {epoch_acc:.4f}')

        if epoch_acc > best_accuracy:
            best_accuracy = epoch_acc
            best_weights = copy.deepcopy(model.state_dict())
        epoch_accuracies.append(epoch_acc)
        print()

    print(f'Training duration: {datetime.now() - start_time}')
    print('Best val Acc: {:4f}'.format(best_accuracy))

    model.load_state_dict(best_weights)
    return model, epoch_accuracies


def training_step(model, dataloader, criterion, optimizer, is_eval: bool):
    running_loss = 0.0
    running_corrects = 0
    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        with torch.set_grad_enabled(True):
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            _, preds = torch.max(outputs, 1)
            if not is_eval:
                loss.backward()
                optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        running_corrects += torch.sum(preds == labels.data)
    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = running_corrects / len(dataloader.dataset)
    return epoch_acc, epoch_loss


model_ft = models.resnet18(pretrained=True)
model_ft.fc = nn.Linear(model_ft.fc.in_features, num_classes)
input_size = 224
print(model_ft)

data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(input_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(input_size),
        transforms.CenterCrop(input_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

print("Initializing Datasets and Dataloaders...")

image_datasets = {x: datasets.ImageFolder(os.path.join(data_dir, x), data_transforms[x]) for x in ['train', 'val']}
dataloaders_dict = {
    x: torch.utils.data.DataLoader(image_datasets[x], batch_size=batch_size, shuffle=True, num_workers=4) for x in
    ['train', 'val']}

model_ft = model_ft.to(device)
params_to_update = model_ft.parameters()
print("Params to learn:")
for name, param in model_ft.named_parameters():
    if param.requires_grad:
        print(f'\t{name}')

optimized_model, epoch_accuracy = train_model(
    model=model_ft,
    dataloaders=dataloaders_dict,
    criterion=nn.CrossEntropyLoss(),
    optimizer=optim.SGD(params_to_update, lr=0.001, momentum=0.9),
    num_epochs=num_epochs
)

spark.read.format("image") \
    .load("/mnt/w210_capstone/Images/lilascience/leopard/leopard.coco/images/train2022/") \
    .filter("image.nChannels > 2") \
    .filter("image.height > 0") \
    .filter("image.width > 0")
