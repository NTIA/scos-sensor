import logging
from os import path

from scos_actions.calibration.calibration import Calibration, load_from_json

logger = logging.getLogger(__name__)


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
            default = check_for_default_calibration(sigan_cal_file_path,default_cal_file_path, "Sigan")
            sigan_cal = load_from_json(sigan_cal_file_path)
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
        sensor_cal = load_from_json(sensor_cal_file_path)
        sensor_cal.is_default = default
    except Exception:
        sensor_cal = None
        logger.exception("Unable to load sensor calibration data, reverting to none")
    return sensor_cal


def check_for_default_calibration(cal_file_path: str,default_cal_path: str, cal_type: str) -> bool:
    default_cal = False
    if cal_file_path == default_cal_path:
        default_cal = True
        logger.warning(
            f"***************LOADING DEFAULT {cal_type} CALIBRATION***************"
        )
    return default_cal
