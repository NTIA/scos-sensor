import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from hardware import radio
from scheduler import scheduler

from .serializers import LocationSerializer
from .utils import get_location
from scos_actions.utils import get_datetime_str_now

logger = logging.getLogger(__name__)


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    sensor_def = get_location()
    if sensor_def:
        return LocationSerializer(sensor_def).data
    else:
        return None


# def get_last_calibration_time():
#     """Returns datetime string of last calibration time"""
#     if radio.is_available and radio.sensor_calibration:
#         cal_datetime = radio.sensor_calibration.calibration_datetime
#         return utils.convert_string_to_millisecond_iso_format(cal_datetime)
#     return "unknown"


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    return Response(
        {
            "scheduler": scheduler.thread.status,
            "location": serialize_location(),
            "system_time": get_datetime_str_now(),
            #"last_calibration_time": get_last_calibration_time(),
        }
    )
