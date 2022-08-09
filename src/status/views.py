import logging
import shutil

from rest_framework.decorators import api_view
from rest_framework.response import Response
from scos_actions.utils import get_datetime_str_now

from scheduler import scheduler

from . import last_calibration_time
from .serializers import LocationSerializer
from . import status_monitor
from .utils import get_location

logger = logging.getLogger(__name__)


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    location = get_location()
    if location:
        return LocationSerializer(location).data
    else:
        return None


def disk_usage():
    usage = shutil.disk_usage('/')
    return usage.used / usage.total


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    status_json = {
        "scheduler": scheduler.thread.status,
        "location": serialize_location(),
        "system_time": get_datetime_str_now(),
        "last_calibration_time": last_calibration_time(),
        "disk_usage": disk_usage()
    }
    for component in status_monitor.status_components:
        status_json[component.name] = component.get_status()
    return Response(
        status
    )
