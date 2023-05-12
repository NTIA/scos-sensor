import logging

from django.conf import settings
from rest_framework import serializers

from schedule.serializers import ISOMillisecondDateTimeFormatField

from ..models import Location
from .components import (
    PreselectorStatusSerializer,
    SignalAnalyzerStatusSerializer,
    SwitchStatusSerializer,
)

logger = logging.getLogger(__name__)
logger.debug(str(__name__))


class LocationSerializer(serializers.ModelSerializer):
    modified = ISOMillisecondDateTimeFormatField()

    class Meta:
        model = Location
        exclude = ("id", "active")


class StatusSerializer(serializers.Serializer):
    scheduler = serializers.CharField(required=True)
    location = LocationSerializer(required=True)  # can be null
    system_time = serializers.DateTimeField(settings.DATETIME_FORMAT, required=True)
    start_time = serializers.DateTimeField(settings.DATETIME_FORMAT, required=True)
    last_calibration_datetime = serializers.DateTimeField(
        settings.DATETIME_FORMAT, required=True
    )
    disk_usage = serializers.IntegerField(required=True)
    days_up = serializers.FloatField(required=True)
    preselector = PreselectorStatusSerializer(required=False)
    switches = SwitchStatusSerializer(many=True, required=False)
    signal_analyzer = SignalAnalyzerStatusSerializer(required=True)
    healthy = serializers.BooleanField(required=True)
