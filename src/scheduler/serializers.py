from rest_framework import serializers

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    action_parameters = serializers.JSONField()

    class Meta:
        model = ScheduleEntry
        fields = '__all__'
