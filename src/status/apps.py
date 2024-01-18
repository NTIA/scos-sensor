import logging
from django.apps import AppConfig
from initialization import sensor_loader
from .models import Location
from scos_actions.metadata.utils import construct_geojson_point


logger = logging.getLogger(__name__)

class StatusConfig(AppConfig):
    name = "status"

    def ready(self):
        try:
            location = Location.objects.get(active=True)
            db_location_geojson = construct_geojson_point(
                location.longitude,
                location.latitude,
                location.height
            )
            logger.debug(f"Location found in DB. Updating sensor location to {location}.")
            if sensor_loader.sensor is not None:
                sensor_loader.sensor.location = db_location_geojson
        except Location.DoesNotExist:
            pass
