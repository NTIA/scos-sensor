import importlib
import logging
import os
import sys
from multiprocessing import cpu_count



bind = ":8000"
workers = 1
worker_class = "gthread"
threads = cpu_count()

loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
logger = logging.getLogger(__name__)

def _modify_path():
    """Ensure Django project is on sys.path."""
    from os import path

    project_path = path.join(path.dirname(path.abspath(__file__)), "../src")
    if project_path not in sys.path:
        sys.path.append(project_path)


def post_worker_init(worker):
    """Start scheduler in worker."""
    _modify_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django

    django.setup()
    from scheduler import scheduler
    from initialization import (
        load_preselector,
        load_switches,
    )
    from initialization import (
        copy_driver_files,
        get_sensor_calibration,
        get_sigan_calibration,
        load_actions,
        load_capabilities
    )
    from django.conf import settings
    from status.models import Location
    from scos_actions.hardware.sensor import Sensor
    from scos_actions.metadata.utils import construct_geojson_point
    from scos_actions.signals import register_component_with_status
    from scos_actions.signals import register_signal_analyzer
    from scos_actions.signals import register_sensor

    sigan_module_setting = settings.SIGAN_MODULE
    sigan_module = importlib.import_module(sigan_module_setting)
    logger.info("Creating " + settings.SIGAN_CLASS + " from " + settings.SIGAN_MODULE)
    sigan_constructor = getattr(sigan_module, settings.SIGAN_CLASS)
    sensor_cal = get_sensor_calibration(settings.SENSOR_CALIBRATION_FILE, settings.DEFAULT_CALIBRATION_FILE)
    sigan_cal = get_sigan_calibration(settings.SIGAN_CALIBRATION_FILE, settings.DEFAULT_CALIBRATION_FILE)
    sigan = sigan_constructor(sensor_cal=sensor_cal, sigan_cal=sigan_cal)
    register_component_with_status.send(sigan, component=sigan)
    register_signal_analyzer.send(sigan, signal_analyzer=sigan)

    switches = load_switches(settings.SWITCH_CONFIGS_DIR)
    capabilities = settings.CAPABILITIES
    preselector = load_preselector(settings.PRESELECTOR_CONFIG, settings.PRESELECTOR_MODULE, settings.PRESELECTOR_CLASS, capabilities["sensor"])
    location = None
    if "location" in capabilities["sensor"]:
        try:
            sensor_loc = capabilities["sensor"].pop("location")
            try:
                #if there is an active database location, use it over the value in the sensor def.
                db_location = Location.objects.get(active=True)
                location = construct_geojson_point(db_location.longitude, db_location.latitude, db_location.height)
            except Location.DoesNotExist:
                # This should never occur because status/migrations/0003_auto_20211217_2229.py
                # will load the No DB location. Use sensor def location and save to DB.
                location = construct_geojson_point(
                    sensor_loc["x"],
                    sensor_loc["y"],
                    sensor_loc["z"] if "z" in sensor_loc else None,
                )
                #Save the sensor location from the sensor def to the database
                db_location = Location()
                db_location.longitude = sensor_loc["x"]
                db_location.latitude = sensor_loc["y"]
                db_location.height = sensor_loc["z"]
                db_location.gps = False
                db_location.description = sensor_loc["description"]
                db_location.save()
        except:
            logger.exception("Failed to get sensor location from sensor definition.")


    sensor = Sensor(signal_analyzer=sigan, preselector = preselector, switches = switches, capabilities = capabilities, location = location)
    scheduler.thread.sensor = sensor
    register_sensor.send(sensor, sensor=sensor)
    scheduler.thread.start()


def worker_exit(server, worker):
    """Notify worker process's scheduler thread that it needs to shut down."""
    _modify_path()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor.settings")

    import django

    django.setup()

    from scheduler import scheduler

    scheduler.thread.stop()
