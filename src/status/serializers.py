from rest_framework import serializers

from schedule.serializers import ISOMillisecondDateTimeFormatField

from .models import Location

import logging
logger = logging.getLogger(__name__)
logger.debug(str(__name__))

class LocationSerializer(serializers.ModelSerializer):
    modified = ISOMillisecondDateTimeFormatField()

    class Meta:
        model = Location
        exclude = ("id", "active")
