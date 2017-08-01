from django.db import models
from jsonfield import JSONField

from schedule.models import ScheduleEntry


class Acquisition(models.Model):
    """Map between schedule entries and their task data and metadata."""
    schedule_entry_name = models.ForeignKey(ScheduleEntry,
                                            on_delete=models.PROTECT,
                                            related_name='acquisitions')
    task_id = models.IntegerField()
    metadata = JSONField()
    data = models.BinaryField(null=True)

    class Meta:
        db_table = 'acquisitions'
        unique_together = (('schedule_entry_name', 'task_id'),)

    def __str__(self):
        return '{}/{}'.format(self.schedule_entry_name, self.task_id)
