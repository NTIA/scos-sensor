import datetime
import logging
import shutil

from rest_framework.decorators import api_view
from rest_framework.response import Response

from scheduler import scheduler
from . import sensor_cal
from . import start_time

from its_preselector.web_relay import WebRelay
from its_preselector.preselector import Preselector

from scos_actions.hardware.sigan_iface import SignalAnalyzerInterface
from scos_actions.status import status_registrar
from scos_actions.utils import get_datetime_str_now
from scos_actions.utils import convert_datetime_to_millisecond_iso_format

from .serializers import LocationSerializer
from .utils import get_location


logger = logging.getLogger(__name__)
logger.info('Loading status/views')


def serialize_location():
    """Returns Location object JSON if set or None and logs an error."""
    location = get_location()
    if location:
        return LocationSerializer(location).data
    else:
        return None


def disk_usage():
    usage = shutil.disk_usage('/')
    percent_used = round(100 * usage.used / usage.total)
    logger.info(str(percent_used) + ' disk used')
    return percent_used

def get_days_up():
    elapsed = datetime.datetime.utcnow() - start_time
    days = elapsed.days
    fractional_day = elapsed.seconds / (60 *60*24)
    return days + fractional_day



@api_view()
def status(request, version, format=None):
    """The status overview of the sensor."""
    healthy = True
    status_json = {
        "scheduler": scheduler.thread.status,
        "location": serialize_location(),
        "system_time": get_datetime_str_now(),
        "start_time": convert_datetime_to_millisecond_iso_format(start_time),
        "last_calibration_time": sensor_cal.calibration_datetime,
        "disk_usage": disk_usage(),
        "days_up": get_days_up()
    }
    for component in status_registrar.status_components:
        logger.info('Adding status ' + str(component.name) + ' = ' + str(component.get_status()))
        component_status =  component.get_status()
        if isinstance(component, WebRelay):
            if 'switches' in status_json:
                status_json['switches'].append(component_status)
            else:
                status_json['switches'] = [component_status]
        elif isinstance(component, Preselector):
            status_json['preselector'] = component_status
        elif isinstance(component,SignalAnalyzerInterface):
            status_json['signal_analyzer'] = component_status
        if 'healthy' in component_status:
            healthy = healthy and component_status['healthy']
    status_json['healthy'] = healthy
    return Response(
        status_json
    )
