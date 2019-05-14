from django.db import models
from jsonfield import JSONField

from schedule.models import ScheduleEntry


class Acquisition(models.Model):
    """Map between schedule entries and their task data and metadata.

    Schedule Entry and Task ID map the acquisition to a specific task on the
    sensor, while recording ID allows for a single task to create more than one
    SigMF recording.

    It is an error to create more than one Acquisition with the same schedule
    entry, task id, and recording id.

    """
    schedule_entry = models.ForeignKey(
        ScheduleEntry,
        on_delete=models.PROTECT,
        related_name='acquisitions',
        help_text="The schedule entry relative to the acquisition")
    task_id = models.IntegerField(
        help_text="The id of the task relative to the acquisition")
    recording_id = models.IntegerField(
        default=0,
        help_text="The id of the recording relative to the task")
    sigmf_metadata = JSONField(
        help_text="The sigmf meta data for the acquisition")
    data = models.BinaryField(help_text="", null=True)
    created = models.DateTimeField(
        help_text="The time the acquisition was created", auto_now_add=True)

    class Meta:
        db_table = 'acquisitions'
        ordering = ('created', )
        unique_together = (('schedule_entry', 'task_id', 'recording_id'), )

    def __str__(self):
        return '{}/{}:{}'.format(
            self.schedule_entry.name,
            self.task_id,
            self.recording_id
        )
