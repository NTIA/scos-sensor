import logging
from pathlib import Path
from time import sleep

from django.conf import settings

logger = logging.getLogger(__name__)


def trigger_api_restart_callback(sender, **kwargs):
    logger.warning("triggering API container restart")
    if settings.IN_DOCKER:
        Path(settings.SDR_HEALTHCHECK_FILE).touch()
        sleep(60) # sleep to prevent running next task until restart completed
