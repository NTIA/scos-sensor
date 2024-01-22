import logging
import types
from pathlib import Path
from django.conf import settings
from .action_loader import ActionLoader
from .capabilities_loader import CapabilitiesLoader
from .sensor_loader import SensorLoader
from .status_monitor import StatusMonitor


from utils.signals import register_component_with_status

logger = logging.getLogger(__name__)

status_monitor = StatusMonitor()


def usb_exists() -> bool:
    logger.debug("Checking for USB...")
    if settings.USB_PATH is not None:
        logger.debug("Checking for " + settings.USB_PATH)
        usb = Path(settings.USB_PATH)
        return usb.exists()
    return True


def status_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        status_monitor.add_component(kwargs["component"])
    except:
        logger.exception("Error registering status component")


try:
    register_component_with_status.connect(status_registration_handler)
    usb_exists = usb_exists()
    if usb_exists:
        action_loader = ActionLoader()
        logger.debug("test")
        logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
        capabilities_loader = CapabilitiesLoader()
        logger.debug("Calling sensor loader.")
        sensor_loader = SensorLoader(capabilities_loader.capabilities)
    else:
        action_loader = types.SimpleNamespace()
        action_loader.actions = {}
        capabilities_loader = types.SimpleNamespace()
        capabilities_loader.capabilities = {}
        sensor_loader = types.SimpleNamespace()
        sensor_loader.sensor = types.SimpleNamespace()
        sensor_loader.sensor.signal_analyzer = None
        sensor_loader.preselector = None
        sensor_loader.switches = {}
        sensor_loader.capabilities = {}
        logger.warning("Usb is not ready. Marking container as unhealthy")
        if settings.IN_DOCKER:
            Path(settings.SDR_HEALTHCHECK_FILE).touch()
except Exception as ex:
    logger.error(f"Error during initialization: {ex}")
