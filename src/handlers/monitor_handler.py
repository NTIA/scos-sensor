import logging
import os
from pathlib import Path

from sensor import settings

logger = logging.getLogger(__name__)


def monitor_action_completed_callback(sender, **kwargs):
    healthy = kwargs["radio_healthy"]
    if healthy:
        if os.path.exists(settings.SDR_HEALTHCHECK_FILE):
            Path(settings.SDR_HEALTHCHECK_FILE).unlink()
        logger.info("USRP healthy")
    else:
        logger.warning("USRP unhealthy")
        if settings.IN_DOCKER:
            Path(settings.SDR_HEALTHCHECK_FILE).touch()
