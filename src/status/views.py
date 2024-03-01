import datetime
import logging
import shutil

from its_preselector.preselector import Preselector
from its_preselector.web_relay import WebRelay
from rest_framework.decorators import api_view
from rest_framework.response import Response
from scos_actions.hardware.sigan_iface import SignalAnalyzerInterface
from scos_actions.utils import (
    convert_datetime_to_millisecond_iso_format,
    get_datetime_str_now,
    get_disk_usage,
)

from initialization import sensor_loader, status_monitor
from scheduler import scheduler

from . import start_time
from .serializers import LocationSerializer
from .utils import get_location

logger = logging.getLogger(__name__)
logger.debug("Loading status/views")


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    location = get_location()
    if location:
        return LocationSerializer(location).data
    else:
        return None


def get_days_up():
    """Return the number of days SCOS has been running."""
    elapsed = datetime.datetime.utcnow() - start_time
    days = elapsed.days
    fractional_day = elapsed.seconds / (60 * 60 * 24)
    return round(days + fractional_day, 4)


@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    healthy = True
    status_json = {
        "scheduler": scheduler.thread.status,
        "location": serialize_location(),
        "system_time": get_datetime_str_now(),
        "start_time": convert_datetime_to_millisecond_iso_format(start_time),
        "disk_usage": get_disk_usage(),
        "days_up": get_days_up(),
    }
    if (
        sensor_loader.sensor is not None
        and sensor_loader.sensor.signal_analyzer is not None
        and sensor_loader.sensor.signal_analyzer.sensor_calibration is not None
    ):
        status_json[
            "last_calibration_datetime"
        ] = (
            sensor_loader.sensor.signal_analyzer.sensor_calibration.last_calibration_datetime
        )
    for component in status_monitor.status_components:
        component_status = component.get_status()
        if isinstance(component, WebRelay):
            if "switches" in status_json:
                status_json["switches"].append(component_status)
            else:
                status_json["switches"] = [component_status]
        elif isinstance(component, Preselector):
            status_json["preselector"] = component_status
        elif isinstance(component, SignalAnalyzerInterface):
            status_json["signal_analyzer"] = component_status
        if "healthy" in component_status:
            healthy = healthy and component_status["healthy"]
    status_json["healthy"] = healthy
    return Response(status_json)
