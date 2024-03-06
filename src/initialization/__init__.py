import importlib
import logging
import ray
import time
from pathlib import Path
from django.conf import settings

from utils.signals import register_component_with_status

from .action_loader import ActionLoader
from .capabilities_loader import CapabilitiesLoader
from .sensor_loader import SensorLoader
from .status_monitor import StatusMonitor
from .utils import set_container_unhealthy
from .utils import get_usb_device_exists

from its_preselector.configuration_exception import ConfigurationException
from its_preselector.controlbyweb_web_relay import ControlByWebWebRelay
from its_preselector.preselector import Preselector
from scos_actions.hardware.utils import power_cycle_sigan
from scos_actions import utils
logger = logging.getLogger(__name__)

status_monitor = StatusMonitor()


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


def status_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        status_monitor.add_component(kwargs["component"])
    except:
        logger.exception("Error registering status component")

try:
    sensor_loader = None
    register_component_with_status.connect(status_registration_handler)
    usb_device_exists = get_usb_device_exists()
    action_loader = ActionLoader()
    logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
    capabilities_loader = CapabilitiesLoader()
    switches = load_switches(settings.SWITCH_CONFIGS_DIR)
    preselector = load_preselector(
        settings.PRESELECTOR_CONFIG,
        settings.PRESELECTOR_MODULE,
        settings.PRESELECTOR_CLASS,
        capabilities_loader.capabilities["sensor"]
    )
    if usb_device_exists:
        logger.debug("Calling sensor loader.")
        sensor_loader = SensorLoader(capabilities_loader.capabilities, switches, preselector)

    else:
        if not settings.RUNNING_MIGRATIONS:
            logger.debug("Power cycling sigan")
            power_cycle_sigan(switches)
            time.sleep(1)
            usb_device_exists = get_usb_device_exists()
            if usb_device_exists:
                logger.debug("Found USB device. Initializing sensor.")
                sensor_loader = SensorLoader(capabilities_loader.capabilities, switches, preselector)
            else:
                logger.debug("Cnable to find USB device after power cycling sigan.")
                sensor_loader = None

    if not settings.RUNNING_MIGRATIONS:
        if sensor_loader is None or sensor_loader.sensor is None or not sensor_loader.sensor.signal_analyzer.healthy():
            set_container_unhealthy()
            time.sleep(60)

        if settings.RAY_INIT and not ray.is_initialized():
            # Dashboard is only enabled if ray[default] is installed
            ray.init()
except:
    logger.exception("Error during initialization")
    set_container_unhealthy()