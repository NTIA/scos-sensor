import logging

import pytest
from scos_actions.metadata.utils import construct_geojson_point

from initialization import sensor_loader
from status.models import Location

logger = logging.getLogger(__name__)


@pytest.mark.django_db
def test_db_location_update_handler():
    location = construct_geojson_point(-105.7, 40.5, 0)
    sensor = sensor_loader.sensor
    logger.debug(f"Sensor: {sensor}")
    location = Location()
    location.gps = False
    location.height = 10
    location.longitude = 100
    location.latitude = -1
    location.description = "test"
    location.active = True
    location.save()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == 100
    assert sensor.location["coordinates"][1] == -1
    assert sensor.location["coordinates"][2] == 10


@pytest.mark.django_db
def test_db_location_update_handler_current_location_none():
    sensor = sensor_loader.sensor
    logger.debug(f"Sensor: {sensor}")
    location = Location()
    location.gps = False
    location.height = 10
    location.longitude = 100
    location.latitude = -1
    location.description = "test"
    location.active = True
    location.save()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == 100
    assert sensor.location["coordinates"][1] == -1
    assert sensor.location["coordinates"][2] == 10


@pytest.mark.django_db
def test_db_location_update_handler_not_active():
    sensor = sensor_loader.sensor
    location = construct_geojson_point(-105.7, 40.5, 0)
    sensor.location = location
    logger.debug(f"Sensor = {sensor}")
    location = Location()
    location.gps = False
    location.height = 10
    location.longitude = 100
    location.latitude = -1
    location.description = ""
    location.active = False
    location.save()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == -105.7
    assert sensor.location["coordinates"][1] == 40.5
    assert sensor.location["coordinates"][2] == 0


@pytest.mark.django_db
def test_db_location_deleted_handler():
    location = construct_geojson_point(-105.7, 40.5, 0)
    sensor = sensor_loader.sensor
    location = Location()
    location.gps = False
    location.height = 10
    location.longitude = 100
    location.latitude = -1
    location.description = "test"
    location.active = True
    location.save()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == 100
    assert sensor.location["coordinates"][1] == -1
    assert sensor.location["coordinates"][2] == 10
    location.delete()
    assert sensor.location is None


@pytest.mark.django_db
def test_db_location_deleted_inactive_handler():
    location = construct_geojson_point(-105.7, 40.5, 0)
    sensor = sensor_loader.sensor
    sensor.location = location
    location = Location()
    location.gps = False
    location.height = 10
    location.longitude = 100
    location.latitude = -1
    location.description = "test"
    location.active = True
    location.save()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == 100
    assert sensor.location["coordinates"][1] == -1
    assert sensor.location["coordinates"][2] == 10
    location.active = False
    location.delete()
    assert sensor.location is not None
    assert sensor.location["coordinates"][0] == 100
    assert sensor.location["coordinates"][1] == -1
    assert sensor.location["coordinates"][2] == 10
