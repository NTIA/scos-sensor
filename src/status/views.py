import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from scos_actions.settings import sensor_calibration
from scos_actions.utils import get_datetime_str_now

from scheduler import scheduler

from .serializers import LocationSerializer
from .utils import get_location

logger = logging.getLogger(__name__)


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    location = get_location()
    if location:
        return LocationSerializer(location).data
    else:
        return None


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    return Response(
        {
            "scheduler": scheduler.thread.status,
            "location": serialize_location(),
            "system_time": get_datetime_str_now(),
            "last_calibration_time": sensor_calibration.calibration_datetime,
        }
    )
