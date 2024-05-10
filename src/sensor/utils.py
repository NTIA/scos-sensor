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
