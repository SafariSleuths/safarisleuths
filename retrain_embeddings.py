# Import libraries for creation of custom dataset and dataloader
import os
import glob
from PIL import Image
import torch
import torch.nn as nn
import torchvision
import random
import torchvision
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader, ConcatDataset
import tempfile
# Import libraries for modeling and training
import pytorch_lightning as pl
import lightly
from lightly.models.modules.heads import SimCLRProjectionHead
from lightly.loss import NTXentLoss
from pytorch_lightning.callbacks import EarlyStopping
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import CSVLogger
# Import the S3 client and bucket for image retrieval
from s3_client import s3, s3_bucket

def embedding_num_sample(uploaded_images):
    """
    Parameters:
    uploaded_images: a local file path of uploaded images
    Returns: the number of prior training images to sample from S3
    """
    # The batch size for SimCLR is 128
    batch_size = 128
    # Find the number of uploaded images
    len_uploaded_images = len(glog.glob(uploaded_images + '/*/*'))
    # Set the ratio as 2 old training images for each new one
    ratio = 2
    total_images = ((int(len_uploaded_images * 3) // 128) + 1) * 128
    len_old_images = total_images - len_uploaded_images
    return len_old_images


class EmbeddingImageDataset(Dataset):
    """A custom class to retrieve and transform randomly-selected S3 training images"""
    def __init__(self,s3_resource, s3_bucket, num_imgs):
        self.s3 = s3_resource
        self.num2sample = num_imgs
        self.bucket = s3_bucket
        # Get the training image paths to retrain the embeddings
        self.files = []
        for obj_sum in self.bucket.objects.filter(Prefix='all_animal_recognition/train/'):
        if obj_sum.key.endswith('.jpg'):
            self.files.append(obj_sum.key)
        # Randomly sample the training data to obtain the required image count
        self.selected_imgs = random.sample(self.files, self.num2sample)
        # Get the individual animal ids from their file folders
        self.labels = [x.split('/')[-2] for x in self.files]
        # Map the individual animal id labels to integers
        self.animal_int_labels = [x for x in range(len(self.labels))]
        self.class_to_idx = dict(zip(self.labels, self.animal_int_labels))
        # Set the image resize operation
        self.transform = transforms.Resize((224,224))

    def __len__(self):
        return len(self.selected_imgs)
    
    def __getitem__(self, idx):
        # Get the object name to be downloaded
        img_name = self.selected_imgs[idx]
        # Get the animal string label of the image to be downloaded
        animal = img_name.split('/')[-2]
        # Convert the string label to an integer one
        label = self.class_to_idx[animal]
        # Download the file to a temporary file
        obj = self.bucket.Object(img_name)
        tmp = tempfile.NamedTemporaryFile()
        tmp_name = '{}.jpg'.format(tmp.name)
        with open(tmp_name, 'wb') as f:
            obj.download_fileobj(f)
            f.flush()
            f.close()
            image = Image.open(tmp_name)
        image = self.transform(image)
        return image, label, img_name

class LocalImageDataset(Dataset):
    """A custom dataset for the locally saved images to be used in retraining"""
    def __init__(self, local_img_path, animal_id_map):
        # Get the full file paths of all local images for the re-training
        self.imgs = glob.glob(local_img_path + '/*/*)
        # Set the mapping of their string labels to integers based upon prior S3 images
        self.class_to_idx = animal_id_map
        self.transform = transforms.Resize((224,224))
    
    def __len__(self):
        return len(self.imgs)

    def __getitem__(self, idx):
        # Get the image path and animal label string
        img_path = self.imgs[idx]
        animal_name = img_path.split('/')[-2]
        # Map the animal string label to an integer one
        img_label = self.class_to_idx[animal_name]
        # Open the image and resize it to the required dimensions for Resnet18
        im = Image.open(img_path).convert('RGB')
        im = self.transform(im)
        return im, img_label, img_path


class SimCLRModel(pl.LightningModule):
    """A version of the SimCLR model for embedding re-training"""
    def __init__(self, backbone, projection_head):
        super().__init__()

        # Load the last trained model backbone and projection head for finetuning
        self.backbone = backbone
        self.projection_head = projection_head

        # create our loss with the optional memory bank
        self.criterion = NTXentLoss()
    
    def forward(self, x):
        h = self.backbone(x).flatten(start_dim=1)
        z = self.projection_head(h)
        return z
    
    def training_step(self, batch, batch_idx):
        (x0, x1), _, _ = batch
        z0 = self.forward(x0)
        z1 = self.forward(x1)

        loss = self.criterion(z0, z1)
        self.log('train_loss', loss, on_step=True, on_epoch=True, logger=True)
        return loss
        
    def configure_optimizers(self):
        optim = torch.optim.SGD(
            self.parameters(),
            lr=6e-2,
            momentum=0.9,
            weight_decay=5e-4,
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optim, max_epochs
        )
        return [optim], [scheduler]


def main(uploaded_images, s3_resource, s3_bucket):
    """
    Parameters:
    uploaded_images: a local file path of new images
    s3_resource: an s3 resource object to download the sampled old training images
    s3_bucket: the s3 bucket to be referenced
    Returns:
    updates the SimCLR model backbone for feature extraction and projection head
    """
    
    # Get the number of old training data images to collect from S3
    num2sample = embedding_num_sample(uploaded_images)

    # Create a dataset object of the randomly sampled images from S3
    sampled_train = EmbeddingImageDataset(s3_resource, s3_bucket, num2sample)

    # Create the dataset object of local images
    local_train = LocalImageDataset(uploaded_images, sampled_train.class_to_idx)

    # Concatenate the sampled images from S3 and the local ones
    train_ds = ConcatDataset([sampled_train, local_train])

    # Use the lightly SimCLR collate function to create the augmented transforms
    collate_fn = lightly.data.SimCLRCollateFunction(
        input_size=224,
        )
    # Use the same batch size as the model was initially trained with
    batch_size=128
    num_workers = 2
    
    # Create the dataloaders to train the embeddings and the classifier
    dataloader_train_simclr = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        drop_last=True,
        num_workers=num_workers)

    # Load the saved state dict objections for the backbone and the projection head
    resnet18_new = torchvision.models.resnet18()
    backbone_new = nn.Sequential(*list(resnet18_new.children())[:-1])
    ckpt = torch.load('simclrresnet18embed.pth')
    backbone_new.load_state_dict(ckpt['resnet18_parameters'])

    projection_head_new = SimCLRProjectionHead(512, 512, 128)
    projection_ckpt = torch.load('simclr_projectionhead.pth')
    projection_head_new.load_state_dict(projection_ckpt['projection_parameters'])

    # Create an instance of the SimCLR model with the pretrained backbone and head
    simclrmodel = SimCLRModel(backbone_new, projection_head_new)

    # Use a GPU for training if possible
    gpus = 1 if torch.cuda.is_available() else 0

    # Define the logger to track training loss
    logger = CSVLogger('embedding_train_logs', name='retrain_embeddings')

    # Define the pytorch trainer and allow for early stopping
    stop_callback = EarlyStopping(
        monitor='train_loss', patience=3, verbose=True,mode='min')
    trainer = Trainer(max_epochs=100, gpus=gpus, callbacks=[stop_callback], logger=logger)
    trainer.fit(simclrmodel, dataloader_train_simclr)
    
    # Save the retrained model backbone and projection head
    pretrained_backbone = simclrmodel.backbone
    backbone_state_dict = {
        'resnet18_parameters': pretrained_backbone.state_dict()
    }
    pretrained_projection_head = simclrmodel.projection_head
    projection_head_state_dict = {
        'projection_parameters': pretrained_projection_head.state_dict()
    }
    torch.save(backbone_state_dict, 'simclrresnet18embed_last.pth')
    torch.save(projection_head_state_dict, 'simclr_projection_head_last.pth')

    print('Embedding retraining has completed.')
