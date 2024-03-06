import logging
import sys
from django.conf import settings
from pathlib import Path
from subprocess import check_output


logger = logging.getLogger(__name__)

def set_container_unhealthy():
    if settings.IN_DOCKER:
        logger.warning("Marking container for restart.")
        Path(settings.SDR_HEALTHCHECK_FILE).touch()


def get_usb_device_exists() -> bool:
    logger.debug("Checking for USB...")
    if not settings.RUNNING_TESTS and settings.USB_DEVICE is not None:
        usb_devices = check_output("lsusb").decode(sys.stdout.encoding)
        logger.debug("Checking for " + settings.USB_DEVICE)
        logger.debug("Found " + usb_devices)
        return settings.USB_DEVICE in usb_devices
    return True