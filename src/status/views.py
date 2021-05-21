import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from scos_actions.utils import get_datetime_str_now

from capabilities import capabilities
from scheduler import scheduler
from status.models import Location

from . import last_calibration_time
from .serializers import LocationSerializer
from .utils import get_location

logger = logging.getLogger(__name__)


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    sensor = capabilities["sensor"]
    if "location" in sensor:
        location = sensor["location"]
        # temp location object for serializer
        db_location = Location(
            gps=False,
            latitude=location["y"],
            longitude=location["x"],
        )
        if "description" in location:
            db_location.description = location["description"]
        return LocationSerializer(db_location).data
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
            "last_calibration_time": last_calibration_time(),
        }
    )
