import logging
from rest_framework import serializers
from rest_framework.reverse import reverse

from constants import MAX_ACTION_LENGTH
from schedule.serializers import DateTimeFromTimestampField
from sensor import V1

logger = logging.getLogger(__name__)
logger.debug("***************** scos-sensor/serializers/task.py **************")


class TaskSerializer(serializers.Serializer):
    schedule_entry = serializers.SerializerMethodField()
    action = serializers.CharField(max_length=MAX_ACTION_LENGTH)
    priority = serializers.IntegerField()
    time = DateTimeFromTimestampField(
        read_only=True, help_text="UTC time (ISO 8601) the this task is scheduled for"
    )

    def get_schedule_entry(self, obj):
        request = self.context["request"]
        kws = {"pk": obj.schedule_entry_name}
        kws.update(V1)
        return reverse("schedule-detail", kwargs=kws, request=request)
