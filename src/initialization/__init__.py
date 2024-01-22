import logging
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
    logger.debug("Checking for /dev/bus/usb/002/003")
    usb_exists = usb_exists()
    if usb_exists:
        action_loader = ActionLoader()
        logger.debug("test")
        logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
        capabilities_loader = CapabilitiesLoader()
        logger.debug("Calling sensor loader.")
        sensor_loader = SensorLoader(capabilities_loader.capabilities)
    else:
        logger.warning("Usb is not ready. Marking container as unhealthy")
        if settings.IN_DOCKER:
            Path(settings.SDR_HEALTHCHECK_FILE).touch()
except Exception as ex:
    logger.error(f"Error during initialization: {ex}")
