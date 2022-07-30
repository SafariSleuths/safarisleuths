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
