import logging
from datetime import datetime

from django.conf import settings

logger = logging.getLogger(__name__)


def get_datetime_from_timestamp(ts: int) -> datetime:
    return datetime.fromtimestamp(ts)


def get_timestamp_from_datetime(dt: datetime) -> int:
    """Assumes UTC datetime."""
    return int(dt.timestamp())


def parse_datetime_str(d: str) -> datetime:
    return datetime.strptime(d, settings.DATETIME_FORMAT)


def check_sigan_settings():
    if settings.SIGAN_MODULE is None:
        logger.warning("SIGAN_MODULE setting is not set!")
    if settings.SIGAN_CLASS is None:
        logger.warning("SIGAN_CLASS setting is not set!")


def check_power_cycle_settings():
    if settings.SIGAN_POWER_SWITCH is None:
        logger.warning(
            "SIGAN_POWER_SWITCH is not set. SCOS will not be able to power cycle the signal analyzer if needed."
        )
    if settings.SIGAN_POWER_CYCLE_STATES is None:
        logger.warning(
            "SIGAN_POWER_CYCLE_STATES is not set. SCOS will not be able to power cycle the signal analyzer if needed."
        )


def check_settings():
    check_sigan_settings()
    check_power_cycle_settings()
