from rest_framework import serializers
from scos_actions.utils import (
    convert_datetime_to_millisecond_iso_format,
    parse_datetime_iso_format_str,
)

from sensor.utils import get_datetime_from_timestamp, get_timestamp_from_datetime


class DateTimeFromTimestampField(serializers.DateTimeField):
    """DateTimeField with integer timestamp as internal value."""

    def to_representation(self, ts: int) -> str:
        """Convert integer timestamp to an ISO 8601 datetime string."""
        if ts is None:
            return None

        dt = get_datetime_from_timestamp(ts)
        dt_str = convert_datetime_to_millisecond_iso_format(dt)

        return dt_str

    def to_internal_value(self, dt_str: str) -> int:
        """Parse an ISO 8601 datetime string and return a timestamp integer."""
        if dt_str is None:
            return None

        dt = super().to_internal_value(dt_str)
        return get_timestamp_from_datetime(dt)


class ISOMillisecondDateTimeFormatField(serializers.DateTimeField):
    def to_representation(self, dt: int) -> str:
        """Convert integer timestamp to an ISO 8601 datetime string."""
        if dt is None:
            return None

        dt_str = convert_datetime_to_millisecond_iso_format(dt)
        return dt_str

    def to_internal_value(self, dt_str: str) -> int:
        """Parse an ISO 8601 datetime string and return a timestamp integer."""
        if dt_str is None:
            return None

        return parse_datetime_iso_format_str(dt_str)
