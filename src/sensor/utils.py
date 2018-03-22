from datetime import datetime

from .settings import DATETIME_FORMAT


def get_datetime_from_timestamp(ts):
    return datetime.fromtimestamp(ts)


def get_datetime_str_now():
    return datetime.isoformat(datetime.utcnow()) + 'Z'


def parse_datetime_str(d):
    return datetime.strptime(d, DATETIME_FORMAT)
