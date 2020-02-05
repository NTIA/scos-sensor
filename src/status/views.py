import logging
from datetime import datetime

from rest_framework.decorators import api_view
from rest_framework.response import Response

from hardware import sdr
from scheduler import scheduler
from sensor import utils

from .serializers import LocationSerializer
from .utils import get_location

logger = logging.getLogger(__name__)


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    sensor_def = get_location()
    if sensor_def:
        return LocationSerializer(sensor_def).data
    else:
        return None


def get_last_calibration_time():
    """Returns datetime string of last calibration time"""
    sdr.connect()
    if sdr.is_available and sdr.radio.sensor_calibration:
        cal_datetime = sdr.radio.sensor_calibration.calibration_datetime
        return utils.convert_to_millisecond_iso_format(cal_datetime)
    return "unknown"


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    return Response(
        {
            "scheduler": scheduler.thread.status,
            "location": serialize_location(),
            "system_time": utils.get_datetime_str_now(),
            "last_calibration_time": get_last_calibration_time(),
        }
    )
