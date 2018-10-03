from django.db import models
from jsonfield import JSONField

from schedule.models import ScheduleEntry


class Acquisition(models.Model):
    """Map between schedule entries and their task data and metadata."""
    schedule_entry = models.ForeignKey(
        ScheduleEntry,
        on_delete=models.PROTECT,
        related_name='acquisitions',
        help_text="The schedule entry relative to the acquisition")
    task_id = models.IntegerField(
        help_text="The id of the task relative to the acquisition")
    sigmf_metadata = JSONField(
        help_text="The sigmf meta data for the acquisition")
    data = models.BinaryField(help_text="", null=True)
    created = models.DateTimeField(
        help_text="The time the acquisition was created", auto_now_add=True)

    class Meta:
        db_table = 'acquisitions'
        ordering = ('created', )
        unique_together = (('schedule_entry', 'task_id'), )

    def __str__(self):
        return '{}/{}'.format(self.schedule_entry.name, self.task_id)
