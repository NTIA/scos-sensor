from django.db import models
from jsonfield import JSONField

from schedule.models import ScheduleEntry


class Acquisition(models.Model):
    """Map between schedule entries and their task data and metadata."""
    task_id = models.IntegerField()
    schedule_entry = models.ForeignKey(ScheduleEntry,
                                       on_delete=models.CASCADE,
                                       related_name='acquisitions')
    metadata = JSONField()
    data = models.BinaryField(null=True)

    class Meta:
        db_table = 'acquisitions'
        unique_together = (('id', 'schedule_entry'),)

    def __str__(self):
        return '{}/{}'.format(self.schedule_entry_id, self.task_id)
