import logging
from pathlib import Path

from sensor import settings

logger = logging.getLogger(__name__)


def trigger_api_restart_callback(sender, **kwargs):
    logger.warning("triggering API container restart")
    if settings.IN_DOCKER:
        Path(settings.SDR_HEALTHCHECK_FILE).touch()
