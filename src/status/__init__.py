import datetime
import logging
from .models import Location
from initialization import sensor_loader
from scos_actions.metadata.utils import construct_geojson_point

logger = logging.getLogger(__name__)
logger.debug("********** Initializing status **********")
start_time = sensor_loader.sensor.start_time
try:
    location = Location.objects.get(active=True)
    db_location_geojson = construct_geojson_point(
            location.longitude,
            location.latitude,
            location.height,
    )
    logger.debug(f"Location found in DB. Updating sensor location to {location}.")
    sensor_loader.sensor.location = db_location_geojson
except Location.DoesNotExist:
    #No location, no problem






