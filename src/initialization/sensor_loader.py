import importlib
import logging

from django.conf import settings
from environs import Env
from its_preselector.preselector import Preselector
from scos_actions.hardware.sensor import Sensor
from scos_actions.metadata.utils import construct_geojson_point

from utils.signals import register_component_with_status

from .utils import get_usb_device_exists, set_container_unhealthy

logger = logging.getLogger(__name__)
env = Env()


class SensorLoader:
    _instance = None

    def __init__(
        self, sensor_capabilities: dict, switches: dict, preselector: Preselector
    ):
        if not hasattr(self, "sensor"):
            logger.debug("Sensor has not been loaded. Loading...")
            self._sensor = load_sensor(sensor_capabilities, switches, preselector)
        else:
            logger.debug("Already loaded sensor. ")

    def __new__(
        cls, sensor_capabilities: dict, switches: dict, preselector: Preselector
    ):
        if cls._instance is None:
            logger.debug("Creating the SensorLoader")
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def sensor(self) -> Sensor:
        return self._sensor


def load_sensor(
    sensor_capabilities: dict, switches: dict, preselector: Preselector
) -> Sensor:
    location = None
    if not settings.RUNNING_TESTS:
        # Remove location from sensor definition and convert to geojson.
        # Db may have an updated location, but status module will update it
        # if needed.
        if "location" in sensor_capabilities["sensor"]:
            sensor_loc = sensor_capabilities["sensor"].pop("location")
            location = construct_geojson_point(
                sensor_loc["x"],
                sensor_loc["y"],
                sensor_loc["z"] if "z" in sensor_loc else None,
            )

    sigan = None
    gps = None
    try:
        if not settings.RUNNING_MIGRATIONS:
            if get_usb_device_exists():
                check_for_required_sigan_settings()
                sigan_module_setting = settings.SIGAN_MODULE
                sigan_module = importlib.import_module(sigan_module_setting)
                logger.info(
                    f"Creating {settings.SIGAN_CLASS} from {settings.SIGAN_MODULE}"
                )
                sigan_constructor = getattr(sigan_module, settings.SIGAN_CLASS)
                sigan = sigan_constructor(switches=switches)
                register_component_with_status.send(sigan, component=sigan)

                if settings.GPS_MODULE and settings.GPS_CLASS:
                    gps_module_setting = settings.GPS_MODULE
                    gps_module = importlib.import_module(gps_module_setting)
                    logger.info(
                        "Creating " + settings.GPS_CLASS + " from " + settings.GPS_MODULE
                    )
                    gps_constructor = getattr(gps_module, settings.GPS_CLASS)
                    gps = gps_constructor()
            else:
                logger.warning("Required USB Device does not exist.")
        else:
            logger.info("Running migrations. Not loading signal analyzer.")
    except BaseException as ex:
        logger.warning(f"unable to create signal analyzer: {ex}")
        set_container_unhealthy()

    # Create sensor before handling calibrations
    sensor = Sensor(
        signal_analyzer=sigan,
        # TODO GPS Not Implemented
        capabilities=sensor_capabilities,
        preselector=preselector,
        switches=switches,
        location=location,
        gps=gps,
        sensor_cal=None,
        differential_cal=None,
    )
    return sensor


def check_for_required_sigan_settings():
    error = ""
    raise_exception = False
    if settings.SIGAN_MODULE is None:
        raise_exception = True
        error = "SIGAN_MODULE environment variable must be set. "
    if settings.SIGAN_CLASS is None:
        raise_exception = True
        error += "SIGAN_CLASS environment variable. "
    if raise_exception:
        raise Exception(error)
