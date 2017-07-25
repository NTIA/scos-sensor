from rest_framework import serializers

import actions
from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        exclude = ("next_task_id",)


class TaskSerializer(serializers.Serializer):
    schedule_entry_name = serializers.SlugField()
    task_id = serializers.IntegerField(write_only=True)
    action = serializers.CharField(max_length=actions.MAX_LENGTH)
    priority = serializers.IntegerField()
    time = serializers.IntegerField()
