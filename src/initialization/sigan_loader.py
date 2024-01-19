import importlib
import logging
from os import path
from pathlib import Path
from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay
from scos_actions import utils
from scos_actions.calibration.calibration import Calibration, load_from_json
from environs import Env

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
                except ConfigurationException:
                    logger.error(f"Unable to configure switch defined in: {file_path}")
    except Exception as ex:
        logger.error(f"Unable to load switches {ex}")
    return switch_dict


def get_sigan_calibration(sigan_cal_file_path: str, default_cal_file_path: str) -> Calibration:
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
            logger.warning("No sigan calibration file specified. Not loading calibration file.")
        elif not path.exists(sigan_cal_file_path):
            logger.warning(
                sigan_cal_file_path + " does not exist. Not loading sigan calibration file."
            )
        else:
            logger.debug(f"Loading sigan cal file: {sigan_cal_file_path}")
            default = check_for_default_calibration(sigan_cal_file_path, default_cal_file_path, "Sigan")
            sigan_cal = load_from_json(sigan_cal_file_path, default)
            sigan_cal.is_default = default
    except Exception:
        sigan_cal = None
        logger.exception("Unable to load sigan calibration data, reverting to none")
    return sigan_cal


def get_sensor_calibration(sensor_cal_file_path: str, default_cal_file_path: str) -> Calibration:
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


def check_for_default_calibration(cal_file_path: str, default_cal_path: str, cal_type: str) -> bool:
    default_cal = False
    if cal_file_path == default_cal_path:
        default_cal = True
        logger.warning(
            f"***************LOADING DEFAULT {cal_type} CALIBRATION***************"
        )
    return default_cal

env = Env()
switches = load_switches(Path(env("SWITCH_CONFIGS_DIR")))
sensor_cal = get_sensor_calibration(env("SENSOR_CALIBRATION_FILE"), env("DEFAULT_CALIBRATION_FILE"))
sigan_cal = get_sigan_calibration(env("SIGAN_CALIBRATION_FILE"), env("DEFAULT_CALIBRATION_FILE"))
signal_analyzer = None
try:
    if not env("RUNNING_MIGRATIONS"):
        sigan_module_setting = env("SIGAN_MODULE")
        sigan_module = importlib.import_module(sigan_module_setting)
        logger.info("Creating " + env("SIGAN_CLASS") + " from " + env("SIGAN_MODULE"))
        sigan_constructor = getattr(sigan_module, env("SIGAN_CLASS"))
        signal_analyzer = sigan_constructor(sensor_cal=sensor_cal, sigan_cal=sigan_cal, switches = switches)
    else:
        logger.info("Running migrations. Not loading signal analyzer.")
except Exception as ex:
    logger.warning(f"unable to create signal analyzer: {ex}")

