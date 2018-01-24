from django.db import models

from schedule.models import ScheduleEntry
from sensor.settings import MAX_TASK_RESULTS
from .consts import MAX_DETAIL_LEN


class TaskResult(models.Model):
    """Map between schedule entries and their task results."""
    schedule_entry = models.ForeignKey(
        ScheduleEntry,
        related_name='results',
        help_text="The schedule entry relative to the result"
    )
    task_id = models.IntegerField(
        help_text="The id of the task relative to the result"
    )
    started = models.DateTimeField(help_text="The time the task started")
    finished = models.DateTimeField(help_text="The time the task finished")
    duration = models.DurationField(help_text="Task duration in seconds")
    result = models.CharField(max_length=7, help_text='"success" or "failure"')
    detail = models.CharField(
        max_length=MAX_DETAIL_LEN,
        blank=True,
        help_text="Arbitrary detail string"
    )

    class Meta:
        ordering = ('task_id',)
        unique_together = (('schedule_entry', 'task_id'),)

    def __init__(self, *args, **kwargs):
        super(TaskResult, self).__init__(*args, **kwargs)

        # Allow Swapping max_results for testing
        self.max_results = MAX_TASK_RESULTS

    def save(self):
        """Limit number of results to MAX_TASK_RESULTS by removing oldest."""
        objects = TaskResult.objects.all()
        if objects.count() >= self.max_results:
            objects[0].delete()

        super(TaskResult, self).save()

    def __str__(self):
        s = "{}/{}"
        return s.format(self.schedule_entry.name, self.task_id)
