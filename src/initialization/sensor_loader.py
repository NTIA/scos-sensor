import importlib
import logging
from os import path


from django.conf import settings
from its_preselector.preselector import Preselector
from scos_actions.calibration.calibration import Calibration, load_from_json
from scos_actions.hardware.sensor import Sensor
from scos_actions.metadata.utils import construct_geojson_point

from utils.signals import register_component_with_status
from .utils import set_container_unhealthy


logger = logging.getLogger(__name__)


class SensorLoader:
    _instance = None

    def __init__(self, sensor_capabilities: dict, switches: dict, preselector: Preselector):
        if not hasattr(self, "sensor"):
            logger.debug("Sensor has not been loaded. Loading...")
            self._sensor = load_sensor(sensor_capabilities, switches)
        else:
            logger.debug("Already loaded sensor. ")

    def __new__(cls, sensor_capabilities):
        if cls._instance is None:
            logger.debug("Creating the SensorLoader")
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def sensor(self) -> Sensor:
        return self._sensor


def load_sensor(sensor_capabilities: dict, switches: dict) -> Sensor:
    switches = {}
    sigan_cal = None
    sensor_cal = None
    preselector = None
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

        sensor_cal = get_sensor_calibration(
            settings.SENSOR_CALIBRATION_FILE, settings.DEFAULT_CALIBRATION_FILE
        )
        sigan_cal = get_sigan_calibration(
            settings.SIGAN_CALIBRATION_FILE, settings.DEFAULT_CALIBRATION_FILE
        )


    sigan = None
    try:
        if not settings.RUNNING_MIGRATIONS:
            check_for_required_sigan_settings()
            sigan_module_setting = settings.SIGAN_MODULE
            sigan_module = importlib.import_module(sigan_module_setting)
            logger.info(
                "Creating " + settings.SIGAN_CLASS + " from " + settings.SIGAN_MODULE
            )
            sigan_constructor = getattr(sigan_module, settings.SIGAN_CLASS)
            sigan = sigan_constructor(
                sensor_cal=sensor_cal, sigan_cal=sigan_cal, switches=switches
            )
            register_component_with_status.send(sigan, component=sigan)
        else:
            logger.info("Running migrations. Not loading signal analyzer.")
    except BaseException as ex:
        logger.warning(f"unable to create signal analyzer: {ex}")
        set_container_unhealthy()

    sensor = Sensor(
        signal_analyzer=sigan,
        capabilities=sensor_capabilities,
        preselector=preselector,
        switches=switches,
        location=location,
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





def get_sigan_calibration(
    sigan_cal_file_path: str, default_cal_file_path: str
) -> Calibration:
    """
    Load signal analyzer calibration data from file.

    :param sigan_cal_file_path: Path to JSON file containing signal
        analyzer calibration data.
    :param default_cal_file_path: Path to the default cal file.
    :return: The signal analyzer ``Calibration`` object.
    """
    try:
        sigan_cal = None
        if sigan_cal_file_path is None or sigan_cal_file_path == "":
            logger.warning(
                "No sigan calibration file specified. Not loading calibration file."
            )
        elif not path.exists(sigan_cal_file_path):
            logger.warning(
                sigan_cal_file_path
                + " does not exist. Not loading sigan calibration file."
            )
        else:
            logger.debug(f"Loading sigan cal file: {sigan_cal_file_path}")
            default = check_for_default_calibration(
                sigan_cal_file_path, default_cal_file_path, "Sigan"
            )
            sigan_cal = load_from_json(sigan_cal_file_path, default)
            sigan_cal.is_default = default
    except Exception:
        sigan_cal = None
        logger.exception("Unable to load sigan calibration data, reverting to none")
    return sigan_cal


def get_sensor_calibration(
    sensor_cal_file_path: str, default_cal_file_path: str
) -> Calibration:
    """
    Load sensor calibration data from file.

    :param sensor_cal_file_path: Path to JSON file containing sensor
        calibration data.
    :param default_cal_file_path: Name of the default calibration file.
    :return: The sensor ``Calibration`` object.
    """
    try:
        sensor_cal = None
        if sensor_cal_file_path is None or sensor_cal_file_path == "":
            logger.warning(
                "No sensor calibration file specified. Not loading calibration file."
            )
        elif not path.exists(sensor_cal_file_path):
            logger.warning(
                sensor_cal_file_path
                + " does not exist. Not loading sensor calibration file."
            )
        else:
            logger.debug(f"Loading sensor cal file: {sensor_cal_file_path}")
            default = check_for_default_calibration(
                sensor_cal_file_path, default_cal_file_path, "Sensor"
            )
        sensor_cal = load_from_json(sensor_cal_file_path, default)
        sensor_cal.is_default = default
    except Exception:
        sensor_cal = None
        logger.exception("Unable to load sensor calibration data, reverting to none")
    return sensor_cal


def check_for_default_calibration(
    cal_file_path: str, default_cal_path: str, cal_type: str
) -> bool:
    default_cal = False
    if cal_file_path == default_cal_path:
        default_cal = True
        logger.warning(
            f"***************LOADING DEFAULT {cal_type} CALIBRATION***************"
        )
    return default_cal
