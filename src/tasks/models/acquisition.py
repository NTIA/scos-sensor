from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete
from jsonfield import JSONField

from .task_result import TaskResult

from django.db.models.signals import pre_delete
from django.db.models.fields.files import FileField
# from .encrypted_storage import EncryptedStorage
# from django.core.files.storage import FileSystemStorage


# def select_storage():
#     return EncryptedStorage() if settings.ENCRYPT_DATA_FILES else FileSystemStorage()


class Acquisition(models.Model):
    """The data and metadata associated with a task.

    Task Result maps the acquisition to a specific task on the sensor, while
    recording ID allows for a single task to create more than one SigMF
    recording.

    It is an error to create more than one Acquisition associated with the same
    task result with the same recording id.

    """

    task_result = models.ForeignKey(
        TaskResult,
        on_delete=models.CASCADE,
        related_name="data",
        help_text="The task_result relative to the acquisition",
    )
    recording_id = models.IntegerField(
        default=1, help_text="The id of the recording relative to the task"
    )
    metadata = JSONField(help_text="The sigmf meta data for the acquisition")
    data = FileField(upload_to="blob/%Y/%m/%d/%H/%M/%S", null=True)
    data_encrypted = models.BooleanField(default=False)


    class Meta:
        db_table = "acquisitions"
        ordering = ("task_result", "recording_id")
        unique_together = (("task_result", "recording_id"),)

    def __str__(self):
        return "{}/{}:{}".format(
            self.task_result.schedule_entry.name,
            self.task_result.task_id,
            self.recording_id,
        )


def clean_up_data(sender, **kwargs):
    acq = kwargs["instance"]
    acq.data.delete(save=False)


pre_delete.connect(clean_up_data, sender=Acquisition)
