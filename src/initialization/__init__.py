import logging

from .action_loader import ActionLoader
from .capabilities_loader import CapabilitiesLoader
from .sensor_loader import SensorLoader
from .status_monitor import StatusMonitor

from utils.signals import register_component_with_status

logger = logging.getLogger(__name__)

status_monitor = StatusMonitor()

def status_registration_handler(sender, **kwargs):
    try:
        logger.debug(f"Registering {sender} as status provider")
        status_monitor.add_component(kwargs["component"])
    except:
        logger.exception("Error registering status component")
try:
    register_component_with_status.connect(status_registration_handler)

    action_loader = ActionLoader()
    logger.debug("test")
    logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
    capabilities_loader = CapabilitiesLoader()
    logger.debug("Calling sensor loader.")
    sensor_loader = SensorLoader(capabilities_loader.capabilities)
except Exception as ex:
    logger.error(f"Error during initialization: {ex}")
