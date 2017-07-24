from rest_framework import serializers

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        exclude = ("next_task_id",)
