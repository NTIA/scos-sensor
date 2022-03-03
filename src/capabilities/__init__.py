import copy
from scos_actions.capabilities import capabilities
from sensor import settings
from sensor.settings import SENSOR_DEFINITION_FILE


def get_sigmf_location():
    from status.models import Location

    try:
        db_location = Location.objects.get(active=True)
        return {
            "x": db_location.longitude,
            "y": db_location.latitude,
            "z": db_location.height,
            "description": db_location.description,
        }
    except Location.DoesNotExist:
        return None


def get_capabilities():
    updated_capabilities = copy.deepcopy(capabilities)
    updated_capabilities["sensor"]["id"] = settings.FQDN
    location = get_sigmf_location()
    if location:
        updated_capabilities["sensor"]["location"] = location
    else:
        if "location" in updated_capabilities['sensor']:
            del updated_capabilities["sensor"]["location"]
    return updated_capabilities
