import multiprocessing
import os
from typing import Callable

import lightly
import pytorch_lightning as pl
import torch
import torch.nn as nn
import torchvision
from lightly.loss import NTXentLoss
from lightly.models.modules.heads import SimCLRProjectionHead
from pytorch_lightning import Trainer, Callback
from pytorch_lightning.callbacks import EarlyStopping
from torch.utils.data import DataLoader

from api.retraining.embeddings_train_dataset import EmbeddingsTrainDataset
from api.retraining.retrain_embeddings_logger import RetrainEmbeddingsLogger

TRAINING_BATCH_SIZE = 320
TRAINING_WORKERS = multiprocessing.cpu_count()
TRAINING_MAX_EPOCHS = 100

BACKBONE_MODEL_PATH = 'models/simclrresnet18embed.pth'
PROJECTION_HEAD_MODEL_PATH = 'models/simclr_projectionhead.pth'


def embedding_num_sample(len_new_images: int):
    """
    Parameters:
    uploaded_images: a local file path of uploaded images
    Returns: the number of prior training images to sample from S3
    """
    total_images = ((int(len_new_images * 3) // TRAINING_BATCH_SIZE) + 1) * TRAINING_BATCH_SIZE
    len_old_images = total_images - len_new_images
    return len_old_images


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
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optim, TRAINING_MAX_EPOCHS)
        return [optim], [scheduler]


class ShouldAbortCallback(Callback):
    def __init__(self, should_abort: Callable[[], bool]):
        super().__init__()
        self.__should_abort = should_abort

    def on_train_epoch_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        if self.__should_abort():
            trainer.should_stop = True

    def on_validation_end(self, trainer: "pl.Trainer", pl_module: "pl.LightningModule") -> None:
        if self.__should_abort():
            trainer.should_stop = True


def retrain_embeddings(
        should_abort: Callable[[], bool],
        train_dataset: EmbeddingsTrainDataset,
        logger: RetrainEmbeddingsLogger
):
    # Use the lightly SimCLR collate function to create the augmented transforms
    collate_fn = lightly.data.SimCLRCollateFunction(input_size=224)

    # Create the dataloaders to train the embeddings and the classifier
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=TRAINING_BATCH_SIZE,
        shuffle=True,
        collate_fn=collate_fn,
        drop_last=True,
        num_workers=TRAINING_WORKERS
    )

    # Load the saved state dict objections for the backbone and the projection head
    resnet18 = torchvision.models.resnet18()
    backbone = nn.Sequential(*list(resnet18.children())[:-1])
    ckpt = torch.load(BACKBONE_MODEL_PATH)
    backbone.load_state_dict(ckpt['resnet18_parameters'])

    project_head = SimCLRProjectionHead(512, 512, 128)
    projection_ckpt = torch.load(PROJECTION_HEAD_MODEL_PATH)
    project_head.load_state_dict(projection_ckpt['projection_parameters'])

    # Create an instance of the SimCLR model with the pretrained backbone and head
    simclr_model = SimCLRModel(backbone, project_head)

    # Define the pytorch trainer and allow for early stopping
    early_stopping_callback = EarlyStopping(monitor='train_loss', patience=3, verbose=True, mode='min')
    should_abort_callback = ShouldAbortCallback(should_abort)
    os.makedirs('embedding_train_logs', exist_ok=True)
    Trainer(
        max_epochs=TRAINING_MAX_EPOCHS,
        gpus=1 if torch.cuda.is_available() else 0,
        callbacks=[early_stopping_callback, should_abort_callback],
        logger=logger
    ).fit(simclr_model, train_dataloader)

    # Save the retrained model backbone and projection head
    pretrained_backbone = simclr_model.backbone
    backbone_state_dict = {'resnet18_parameters': pretrained_backbone.state_dict()}
    torch.save(backbone_state_dict, BACKBONE_MODEL_PATH)

    pretrained_projection_head = simclr_model.projection_head
    projection_head_state_dict = {'projection_parameters': pretrained_projection_head.state_dict()}
    torch.save(projection_head_state_dict, PROJECTION_HEAD_MODEL_PATH)

    print('Embedding retraining has completed.')
