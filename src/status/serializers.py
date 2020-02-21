from rest_framework import serializers

from schedule.serializers import ISOMillisecondDateTimeFormatField

from .models import Location


class LocationSerializer(serializers.ModelSerializer):
    modified = ISOMillisecondDateTimeFormatField()

    class Meta:
        model = Location
        exclude = ("id", "active")
