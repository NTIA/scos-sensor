import importlib
import logging
import time
from os import path
from pathlib import Path
from typing import Optional, Union

from django.conf import settings
from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay
from its_preselector.preselector import Preselector
from scos_actions.calibration.differential_calibration import DifferentialCalibration
from scos_actions.calibration.sensor_calibration import SensorCalibration
from scos_actions.hardware.utils import power_cycle_sigan
from scos_actions.utils import load_from_json

from utils.signals import register_component_with_status

from .action_loader import ActionLoader
from .capabilities_loader import CapabilitiesLoader
from .sensor_loader import SensorLoader
from .status_monitor import StatusMonitor
from .utils import get_usb_device_exists, set_container_unhealthy

logger = logging.getLogger(__name__)

status_monitor = StatusMonitor()


def load_preselector_from_file(
    preselector_module, preselector_class, preselector_config_file: Path
):
    if preselector_config_file is None:
        return None
    else:
        try:
            preselector_config = load_from_json(preselector_config_file)
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
    if module and preselector_class_name:
        preselector_module = importlib.import_module(module)
        preselector_constructor = getattr(preselector_module, preselector_class_name)
        preselector_config = load_from_json(preselector_config)
        ps = preselector_constructor(sensor_definition, preselector_config)
        register_component_with_status.send(ps, component=ps)
    else:
        ps = None
    return ps


def load_switches(switch_dir: Path) -> dict:
    logger.debug(f"Loading switches in {switch_dir}")
    switch_dict = {}
    try:
        if switch_dir is not None and switch_dir.is_dir():
            for f in switch_dir.iterdir():
                file_path = f.resolve()
                logger.debug(f"loading switch config {file_path}")
                conf = load_from_json(file_path)
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


def status_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        status_monitor.add_component(kwargs["component"])
    except:
        logger.exception("Error registering status component")


def set_container_unhealthy():
    if settings.IN_DOCKER:
        logger.warning("Signal analyzer is not healthy. Marking container for restart.")
        Path(settings.SDR_HEALTHCHECK_FILE).touch()


def get_calibration(
    cal_file_path: str, cal_type: str
) -> Optional[Union[DifferentialCalibration, SensorCalibration]]:
    """
    Load calibration data from file.

    :param cal_file_path: Path to the JSON calibration file.
    :param cal_type: Calibration type to load: "sensor" or "differential"
    :return: The ``Calibration`` object, if loaded, or ``None`` if loading failed.
    """
    try:
        cal = None
        if cal_file_path is None or cal_file_path == "":
            logger.error("No calibration file specified, reverting to none.")
        elif not path.exists(cal_file_path):
            logger.error(f"{cal_file_path} does not exist, reverting to none.")
        else:
            logger.debug(f"Loading calibration file: {cal_file_path}")
            # Create calibration object
            cal_file_path = Path(cal_file_path)
            if cal_type.lower() in ["sensor", "onboard"]:
                cal = SensorCalibration.from_json(cal_file_path)
            elif cal_type.lower() == "differential":
                cal = DifferentialCalibration.from_json(cal_file_path)
            else:
                logger.error(f"Unknown calibration type: {cal_type}")
                raise ValueError
    except Exception:
        cal = None
        logger.exception(
            f"Unable to load {cal_type} calibration file from {cal_file_path}."
            + " Reverting to none"
        )
    finally:
        return cal


try:
    sensor_loader = None
    register_component_with_status.connect(status_registration_handler)
    action_loader = ActionLoader()
    logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
    capabilities_loader = CapabilitiesLoader()
    switches = load_switches(settings.SWITCH_CONFIGS_DIR)
    preselector = load_preselector(
        settings.PRESELECTOR_CONFIG,
        settings.PRESELECTOR_MODULE,
        settings.PRESELECTOR_CLASS,
        capabilities_loader.capabilities["sensor"],
    )

    if get_usb_device_exists():
        logger.debug("Initializing Sensor...")
        sensor_loader = SensorLoader(
            capabilities_loader.capabilities, switches, preselector
        )

    else:
        logger.debug("Power cycling sigan")
        try:
            power_cycle_sigan(switches)
        except Exception as power_cycle_exception:
            logger.error(f"Unable to power cycle sigan: {power_cycle_exception}")
        set_container_unhealthy()
        time.sleep(60)

    if not settings.RUNNING_MIGRATIONS:
        if (
            sensor_loader.sensor.signal_analyzer is None
            or not sensor_loader.sensor.signal_analyzer.healthy()
        ):
            try:
                power_cycle_sigan(switches)
            except Exception as power_cycle_exception:
                logger.error(f"Unable to power cycle sigan: {power_cycle_exception}")
            set_container_unhealthy()
            time.sleep(60)

        # Calibration loading
        if not settings.RUNNING_TESTS:
            # Load the onboard cal file as the sensor calibration, if it exists
            onboard_cal = get_calibration(settings.ONBOARD_CALIBRATION_FILE, "sensor")
            if onboard_cal is not None:
                sensor_loader.sensor.sensor_calibration = onboard_cal
            else:
                # Otherwise, try using the sensor calibration file
                sensor_cal = get_calibration(settings.SENSOR_CALIBRATION_FILE, "sensor")
                if sensor_cal is not None:
                    sensor_loader.sensor.sensor_calibration = sensor_cal

            # Now load the differential calibration, if it exists
            differential_cal = get_calibration(
                settings.DIFFERENTIAL_CALIBRATION_FILE,
                "differential",
            )
            sensor_loader.sensor.differential_calibration = differential_cal

        import ray

        if settings.RAY_INIT and not ray.is_initialized():
            # Dashboard is only enabled if ray[default] is installed
            logger.debug("Initializing ray.")
            ray.init()
except BaseException as error:
    logger.exception(f"Error during initialization: {error}")
    set_container_unhealthy()
