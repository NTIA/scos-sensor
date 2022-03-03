import copy

from sensor import settings
from sensor.settings import SENSOR_DEFINITION_FILE


def load_from_json(fname):
    import json
    import logging

    logger = logging.getLogger(__name__)

    try:
        with open(fname) as f:
            return json.load(f)
    except Exception:
        logger.exception("Unable to load JSON file {}".format(fname))


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


_capabilities = {}
_capabilities["sensor"] = load_from_json(SENSOR_DEFINITION_FILE)
_capabilities["sensor"]["id"] = settings.FQDN


def get_capabilities():
    capabilities = copy.deepcopy(_capabilities)
    location = get_sigmf_location()
    if location:
        capabilities["sensor"]["location"] = location
    #else:
    #    del capabilities["sensor"]["location"]
    return capabilities
