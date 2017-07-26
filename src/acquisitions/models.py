from django.db import models
from jsonfield import JSONField

from scheduler.models import ScheduleEntry


class Acquisition(models.Model):
    """Map between event descriptors and their event data and metadata."""
    task_id = models.IntegerField(primary_key=True)
    schedule_entry = models.ForeignKey(ScheduleEntry, on_delete=models.CASCADE)
    metadata = JSONField()
    data = models.BinaryField(null=True)

    class Meta:
        db_table = 'acquisitions'
        unique_togher = (('schedule_entry', 'task_id'))

    def __str__(self):
        return '{}/{}'.format(self.schedule_entry_id, self.task_id)
