import datetime

from django.db import models
from django.utils import timezone

from schedule.models import ScheduleEntry
from sensor.settings import MAX_TASK_RESULTS
from tasks.consts import MAX_DETAIL_LEN

UTC = timezone.timezone.utc


class TaskResult(models.Model):
    """Map between schedule entries and their task results."""

    SUCCESS = 1
    FAILURE = 2
    IN_PROGRESS = 3
    RESULT_CHOICES = (
        (SUCCESS, "success"),
        (FAILURE, "failure"),
        (IN_PROGRESS, "in-progress"),
    )

    schedule_entry = models.ForeignKey(
        ScheduleEntry,
        on_delete=models.PROTECT,
        related_name="task_results",
        help_text="The schedule entry relative to the result",
    )
    task_id = models.IntegerField(help_text="The id of the task relative to the result")
    started = models.DateTimeField(
        default=datetime.datetime(2019, 5, 16, 23, tzinfo=UTC),
        help_text="The time the task started",
    )
    finished = models.DateTimeField(
        default=datetime.datetime(2019, 5, 16, 23, tzinfo=UTC),
        help_text="The time the task finished",
    )
    duration = models.DurationField(
        default=timezone.ZERO, help_text="Task duration in seconds"
    )
    status = models.CharField(
        default="in-progress",
        max_length=11,
        help_text='"success" or "failure"',
        choices=RESULT_CHOICES,
    )
    detail = models.CharField(
        max_length=MAX_DETAIL_LEN, blank=True, help_text="Arbitrary detail string"
    )

    class Meta:
        ordering = ("task_id",)
        unique_together = (("schedule_entry", "task_id"),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Allow Swapping max_results for testing
        self.max_results = MAX_TASK_RESULTS

    def save(self):
        """Limit number of results to MAX_TASK_RESULTS by removing oldest."""
        all_results = TaskResult.objects.all()
        filter = {"schedule_entry__name": self.schedule_entry.name}
        same_entry_results = all_results.filter(**filter)
        if same_entry_results.count() >= self.max_results:
            same_entry_results[0].delete()

        super().save()

    def __str__(self):
        s = "{}/{}"
        return s.format(self.schedule_entry.name, self.task_id)
