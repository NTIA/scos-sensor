from datetime import datetime

from django.conf import settings

from sensor import utils


def test_timestamp_manipulation():
    now = datetime.now()
    now_int = int(now.timestamp())
    now_fromint = datetime.fromtimestamp(now_int)
    now_str = now.strftime(settings.DATETIME_FORMAT)

    test_dt_int = utils.get_timestamp_from_datetime(now)
    test_dt_fromint = utils.get_datetime_from_timestamp(now_int)
    test_dt_fromstr = utils.parse_datetime_str(now_str)

    assert now_int == test_dt_int
    assert now_fromint == test_dt_fromint
    assert now == test_dt_fromstr
