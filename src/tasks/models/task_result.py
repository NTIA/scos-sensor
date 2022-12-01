import datetime
import logging
import os
import shutil

from django.db import models
from django.utils import timezone

from schedule.models import ScheduleEntry
from sensor.settings import MAX_DISK_USAGE
from tasks.consts import MAX_DETAIL_LEN

UTC = timezone.timezone.utc

logger = logging.getLogger(__name__)


class TaskResult(models.Model):
    """Map between schedule entries and their task results."""

    SUCCESS = 1
    FAILURE = 2
    IN_PROGRESS = 3
    NOTIFICATION_FAILED = 4
    RESULT_CHOICES = (
        (SUCCESS, "success"),
        (FAILURE, "failure"),
        (IN_PROGRESS, "in-progress"),
        (NOTIFICATION_FAILED, "notification_failed"),
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
        default=datetime.timedelta(), help_text="Task duration in seconds"
    )
    status = models.CharField(
        default="in-progress",
        max_length=19,
        help_text='"success", "failure", or "notification_failed"',
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

        # Allow Swapping max_disk_usage for testing
        self.max_disk_usage = MAX_DISK_USAGE

    def save(self):
        """Limit disk usage to MAX_DISK_USAGE by removing oldest result."""
        filter = {"schedule_entry__name": self.schedule_entry.name}

        same_entry_results = TaskResult.objects.filter(**filter).order_by("id")
        if (
            same_entry_results.count() > 0 and same_entry_results[0].id != self.id
        ):  # prevent from deleting this task result's acquisition
            acquisitions = same_entry_results[0].data
            if acquisitions.count() > 0:
                data_path = os.path.dirname(acquisitions.all()[0].data.path)
                disk_space = shutil.disk_usage(data_path)
                percent_used = (disk_space.used / disk_space.total) * 100
                if percent_used > self.max_disk_usage:
                    logger.info("Max disk usage exceeded, deleting oldest task result!")
                    same_entry_results[0].delete()

        super().save()

    def __str__(self):
        s = "{}/{}"
        return s.format(self.schedule_entry.name, self.task_id)
