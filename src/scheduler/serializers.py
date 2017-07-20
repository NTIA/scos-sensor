from rest_framework import serializers

from .models import ScheduleEntry


class ScheduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = '__all__'
