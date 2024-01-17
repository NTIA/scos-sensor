import logging
from initialization import sensor_loader
from status.models import GPS_LOCATION_DESCRIPTION, Location
from scos_actions.metadata.utils import construct_geojson_point

logger = logging.getLogger(__name__)

def location_action_completed_callback(sender, **kwargs):
    """Update database when GPS is synced or database is updated"""
    logger.debug(f"Updating location from {sender}")
    latitude = kwargs["latitude"] if "latitude" in kwargs else None
    longitude = kwargs["longitude"] if "longitude" in kwargs else None
    gps = kwargs["gps"] if "gps" in kwargs else None
    description = kwargs["description"] if "description" in kwargs else None
    height = kwargs["height"] if "height" in kwargs else None

    try:
        location = Location.objects.get(active=True)
    except Location.DoesNotExist:
        location = Location()
    if latitude and longitude:
        location.latitude = latitude
        location.longitude = longitude
    if gps:
        location.gps = True
    if description:
        location.description = description
    if height:
        location.height = height
    location.active = True
    location.save()


def db_location_updated(sender, **kwargs):
    instance = kwargs["instance"]
    logger.debug(f"DB location updated by {sender}")
    if isinstance(instance, Location) and instance.active:
        geojson = construct_geojson_point(longitude = instance.longitude, latitude=instance.latitude, altitude= instance.height)
        if sensor_loader.sensor:
            sensor_loader.sensor.location = geojson
            logger.debug(f"Updated {sensor_loader.sensor} location to {geojson}")
        else:
            logger.warning("No sensor is registered. Unable to update sensor location.")


def db_location_deleted(sender, **kwargs):
    instance = kwargs["instance"]
    if isinstance(instance, Location):
        if instance.active:
            if sensor_loader.sensor:
                sensor_loader.sensor.location = None
                logger.debug(f"Set {sensor_loader.sensor} location to None.")
            else:
                logger.warning("No sensor registered. Unable to remove sensor location.")
