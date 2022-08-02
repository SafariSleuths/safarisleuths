import json
import logging
import shutil
import time
from datetime import datetime
from typing import List, Dict

from torch.utils.data import DataLoader

from api.clients.s3_client import s3_bucket
from api.data_models.annotations import read_annotations_for_collection, Annotation
from api.predictions.predict_individual import load_backbone
from api.retraining.classifier_train_dataset import ClassifierTrainDataset
from api.retraining.embeddings_train_dataset import EmbeddingsTrainDataset
from api.retraining.retrain_classifier import retrain_classifier_for_species, generate_embeddings
from api.retraining.retrain_embeddings import retrain_embeddings, embedding_num_sample, TRAINING_BATCH_SIZE, \
    TRAINING_MAX_EPOCHS, TRAINING_WORKERS
from api.retraining.retrain_embeddings_logger import RetrainEmbeddingsLogger
from api.data_models.retrain_event_log import log_event, RetrainEventLog, truncate_job_logs
from api.data_models.retrain_metrics import truncate_metrics
from api.data_models.retrain_status import read_job_status_from_redis, save_job_status_to_redis, RetrainStatus
from api.data_models.species import Species


class RetrainingOrchestrator:
    def __init__(self, collection_id: str, logger: logging.Logger, classifier_only: bool):
        self.collection_id = collection_id
        self.logger = logger
        self.classifier_only = classifier_only
        self.__version = str(time.time())

    def start_retraining(self) -> None:
        truncate_job_logs(self.collection_id)
        truncate_metrics(self.collection_id)
        job = self.__job_status()
        job['status'] = 'started'
        save_job_status_to_redis(job)
        self.__log_event(f'Started retraining for collection {self.collection_id}.')

        new_annotations = read_annotations_for_collection(self.collection_id)
        new_annotations = [a for a in new_annotations if a['accepted']]
        if len(new_annotations) == 0:
            job['status'] = 'completed'
            save_job_status_to_redis(job)
            self.__log_event('Retraining skipped since there are no new annotations for training.')
            return

        self.__log_event(
            f"Retraining with {len(new_annotations)} new annotation{'s' if len(new_annotations) != 1 else ''}."
        )

        if not self.classifier_only:
            self.__retrain_embeddings(new_annotations)

        if self.__should_abort():
            self.__log_event('Retraining aborted!')
            return

        self.__retrain_classifier(new_annotations)

        if self.__should_abort():
            self.__log_event('Retraining aborted!')
            return

        self.__upload_annotations_to_training(new_annotations)
        self.__log_event(f'New images added to classifier training data for future training.')

        job = self.__job_status()
        job['status'] = 'completed'
        save_job_status_to_redis(job)
        self.__log_event(f'Completed all retraining tasks for collection {self.collection_id}.')

    def __retrain_embeddings(self, new_annotations: List[Annotation]) -> None:
        self.__log_event("Started retraining for the embeddings backbone.")
        self.__log_event(
            f'Batch size: {TRAINING_BATCH_SIZE}, max epochs: {TRAINING_MAX_EPOCHS}, workers: {TRAINING_WORKERS}.'
        )
        num_prior_images = embedding_num_sample(len(new_annotations))
        self.__log_event(f'Fine-tuning with {num_prior_images} images from existing training data.')

        dataset = EmbeddingsTrainDataset(new_annotations=new_annotations, num2sample=num_prior_images)
        logger = RetrainEmbeddingsLogger(collection_id=self.collection_id, version=self.__version)
        start_time = datetime.now()
        retrain_embeddings(should_abort=self.__should_abort, train_dataset=dataset, logger=logger)
        elapsed_time = datetime.now() - start_time

        if self.__should_abort():
            return
        self.__log_event(f'Completed retraining for the embeddings backbone after {elapsed_time.seconds}s.')

    def __retrain_classifier(self, new_annotations: List[Annotation]) -> None:
        backbone, device = load_backbone()
        grouped_annotations = self.__group_annotations_by_species(new_annotations)
        for species in grouped_annotations.keys():
            self.__log_event(f'Found new training data for the {species} classifier.')

        for species, annotations in grouped_annotations.items():
            if self.__should_abort():
                return

            self.__log_event(f'Loading training data for the {species} classifier.')
            train_dataset = ClassifierTrainDataset(species, new_annotations)
            train_dataloader = DataLoader(
                train_dataset,
                batch_size=1,  # Batch size to be 1 so that no training examples are dropped.
                shuffle=True,
                num_workers=2,
                drop_last=True
            )
            load_data_start_time = datetime.now()
            train_embeddings, train_labels = generate_embeddings(backbone, train_dataloader)
            elapsed_time = datetime.now() - load_data_start_time
            self.__log_event(
                f'Loaded {len(train_embeddings)} embeddings for {species} after {elapsed_time.seconds}s.'
            )

            if self.__should_abort():
                return

            self.__log_event(f'Started retraining for the {species} classifier.')
            retrain_start_time = datetime.now()
            retrain_classifier_for_species(
                species=species,
                train_embeddings=train_embeddings,
                train_labels=train_labels
            )
            elapsed_time = datetime.now() - retrain_start_time

            if self.__should_abort():
                return

            with open(species.labels_location(), 'w') as f:
                json.dump(train_dataset.labels, f)

            self.__log_event(f'Completed retraining for the {species} classifier after {elapsed_time.seconds}s.')
            self.logger.info(f'Model saved as {species.model_location()}')

    def __job_status(self) -> RetrainStatus:
        return read_job_status_from_redis(self.collection_id)

    def __log_event(self, message: str) -> None:
        self.logger.info(message)
        log_event(RetrainEventLog(collection_id=self.collection_id, created_at=time.time(), message=message))

    def __should_abort(self) -> bool:
        job = read_job_status_from_redis(self.collection_id)
        if job['status'] == 'aborted':
            return True
        return False

    @staticmethod
    def __group_annotations_by_species(annotations: List[Annotation]) -> Dict[Species, List[Annotation]]:
        results = {}
        for annotation in annotations:
            species = Species.from_string(annotation['predicted_species'])
            if species not in results:
                results[species] = []
            results[species].append(annotation)
        return results

    @staticmethod
    def __upload_annotations_to_training(annotations: List[Annotation]) -> None:
        for annotation in annotations:
            if annotation['accepted'] is False:
                continue

            species = Species.from_string(annotation['predicted_species'])
            if species is None:
                continue

            new_path = f"{species.training_data_location()}/{annotation['predicted_name']}/{annotation['id']}.jpg"
            shutil.copyfile(annotation['cropped_file_name'], new_path)
            if s3_bucket is not None:
                s3_bucket.upload_file(annotation['cropped_file_name'], new_path)
