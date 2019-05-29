import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response

from scheduler import scheduler
from sensor import utils
from .models import Location
from .serializers import LocationSerializer


logger = logging.getLogger(__name__)


def get_location():
    """Returns Location object JSON if set or None and logs an error."""
    try:
        sensor_def = Location.objects.filter(active=True).get()
        return LocationSerializer(sensor_def).data
    except Location.DoesNotExist:
        logger.error("You must create a Location in /admin.")
        return None


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    return Response(
        {
            "scheduler": scheduler.thread.status,
            "location": get_location(),
            "system_time": utils.get_datetime_str_now(),
        }
    )
