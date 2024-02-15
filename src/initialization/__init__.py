import logging
import ray
import sys
import types
from pathlib import Path
from subprocess import check_output

from django.conf import settings

from utils.signals import register_component_with_status

from .action_loader import ActionLoader
from .capabilities_loader import CapabilitiesLoader
from .sensor_loader import SensorLoader
from .status_monitor import StatusMonitor
from .utils import set_container_unhealthy
from .utils import get_usb_device_exists

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
    usb_device_exists = get_usb_device_exists()
    if usb_device_exists:
        action_loader = ActionLoader()
        logger.debug(f"Actions ActionLoader has {len(action_loader.actions)} actions")
        capabilities_loader = CapabilitiesLoader()
        logger.debug("Calling sensor loader.")
        sensor_loader = SensorLoader(capabilities_loader.capabilities)
        if (
            not settings.RUNNING_MIGRATIONS
            and not sensor_loader.sensor.signal_analyzer.healthy()
        ):
            set_container_unhealthy()
        if settings.RAY_INIT:
            if not ray.is_initialized():
                # Dashboard is only enabled if ray[default] is installed
                ray.init()
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
        set_container_unhealthy()
except:
    logger.exception("Error during initialization")
    set_container_unhealthy()