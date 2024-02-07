import importlib
import logging
from os import path
from pathlib import Path
from typing import Union

from django.conf import settings
from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay
from its_preselector.preselector import Preselector
from scos_actions import utils
from scos_actions.calibration.differential_calibration import DifferentialCalibration
from scos_actions.calibration.sensor_calibration import SensorCalibration
from scos_actions.hardware.sensor import Sensor
from scos_actions.metadata.utils import construct_geojson_point

from utils.signals import register_component_with_status

logger = logging.getLogger(__name__)


class SensorLoader:
    _instance = None

    def __init__(self, sensor_capabilities: dict):
        if not hasattr(self, "sensor"):
            logger.debug("Sensor has not been loaded. Loading...")
            self._sensor = load_sensor(sensor_capabilities)
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


def load_sensor(sensor_capabilities: dict) -> Sensor:
    switches = {}
    sensor_cal = None
    differential_cal = None
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
        switches = load_switches(settings.SWITCH_CONFIGS_DIR)
        sensor_cal = get_calibration(
            settings.SENSOR_CALIBRATION_FILE,
            settings.DEFAULT_SENSOR_CALIBRATION_FILE,
            "sensor",
        )
        differential_cal = get_calibration(
            settings.DIFFERENTIAL_CALIBRATION_FILE,
            settings.DEFAULT_DIFFERENTIAL_CALIBRATION_FILE,
            "differential",
        )
        preselector = load_preselector(
            settings.PRESELECTOR_CONFIG,
            settings.PRESELECTOR_MODULE,
            settings.PRESELECTOR_CLASS,
            sensor_capabilities["sensor"],
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
            sigan = sigan_constructor(switches=switches)
            register_component_with_status.send(sigan, component=sigan)
        else:
            logger.info("Running migrations. Not loading signal analyzer.")
    except Exception as ex:
        logger.warning(f"unable to create signal analyzer: {ex}")

    sensor = Sensor(
        signal_analyzer=sigan,
        # TODO GPS Not Implemented
        capabilities=sensor_capabilities,
        preselector=preselector,
        switches=switches,
        location=location,
        sensor_cal=sensor_cal,
        differential_cal=differential_cal,
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


def load_switches(switch_dir: Path) -> dict:
    logger.debug(f"Loading switches in {switch_dir}")
    switch_dict = {}
    try:
        if switch_dir is not None and switch_dir.is_dir():
            for f in switch_dir.iterdir():
                file_path = f.resolve()
                logger.debug(f"loading switch config {file_path}")
                conf = utils.load_from_json(file_path)
                try:
                    switch = ControlByWebWebRelay(conf)
                    logger.debug(f"Adding {switch.id}")
                    switch_dict[switch.id] = switch
                    logger.debug(f"Registering switch status for {switch.name}")
                    register_component_with_status.send(__name__, component=switch)
                except ConfigurationException:
                    logger.error(f"Unable to configure switch defined in: {file_path}")
    except Exception as ex:
        logger.error(f"Unable to load switches {ex}")
    return switch_dict


def load_preselector_from_file(
    preselector_module, preselector_class, preselector_config_file: Path
):
    if preselector_config_file is None:
        return None
    else:
        try:
            preselector_config = utils.load_from_json(preselector_config_file)
            return load_preselector(
                preselector_config, preselector_module, preselector_class
            )
        except ConfigurationException:
            logger.exception(
                f"Unable to create preselector defined in: {preselector_config_file}"
            )
    return None


def load_preselector(
    preselector_config: str,
    module: str,
    preselector_class_name: str,
    sensor_definition: dict,
) -> Preselector:
    logger.debug(
        f"loading {preselector_class_name} from {module} with config: {preselector_config}"
    )
    if module is not None and preselector_class_name is not None:
        preselector_module = importlib.import_module(module)
        preselector_constructor = getattr(preselector_module, preselector_class_name)
        preselector_config = utils.load_from_json(preselector_config)
        ps = preselector_constructor(sensor_definition, preselector_config)
        register_component_with_status.send(ps, component=ps)
    else:
        ps = None
    return ps


def get_calibration(
    cal_file_path: str, default_cal_file_path: str, cal_type: str
) -> Union[DifferentialCalibration, SensorCalibration]:
    """
    Load calibration data from file.

    :param cal_file_path: Path to the JSON calibration file.
    :param default_cal_file_path: Path to the default calibration file.
    :param cal_type: Calibration type to load, either "sensor" or "differential"
    :return: The ``Calibration`` object.
    """
    try:
        cal = None
        if cal_file_path is None or cal_file_path == "":
            logger.error("No calibration file specified.")
            raise ValueError
        elif not path.exists(cal_file_path):
            logger.error(f"{cal_file_path} does not exist.")
            raise FileNotFoundError
        else:
            logger.debug(f"Loading calibration file: {cal_file_path}")
            default = check_for_default_calibration(
                cal_file_path, default_cal_file_path, cal_type
            )
            # Create calibration object
            if cal_type.lower() == "sensor":
                cal = SensorCalibration.from_json(cal_file_path, default)
            elif cal_type.lower() == "differential":
                cal = DifferentialCalibration.from_json(cal_file_path, default)
            else:
                logger.error(f"Unknown calibration type: {cal_type}")
                raise ValueError
    except Exception:
        cal = None
        logger.exception("Unable to load calibration file, reverting to none")
    finally:
        return cal


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
