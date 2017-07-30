import itertools
from itertools import count

import pytest
from django.core.exceptions import ValidationError

from .utils import flatten
from scheduler import utils
from schedule.models import ScheduleEntry, DEFAULT_PRIORITY


@pytest.mark.parametrize('test_input,future_t,expected', [
    ((0, 5, 1), 2, [[0, 1], [2, 3], [4]]),
    ((1, 5, 2), 8, [[1, 3]])
])
def test_take_until(test_input, future_t, expected):
    start, stop, interval = test_input
    entry = ScheduleEntry(name='t', start=start, stop=stop, interval=interval,
                          action='logger')
    initial_times = list(entry.get_remaining_times())
    r = []
    for t in count(future_t, future_t):
        ts = list(entry.take_until(t))
        if not ts:
            break
        r.append(ts)

    assert r == expected
    assert initial_times == list(flatten(r))


def test_undefined_start_is_now():
    entry = ScheduleEntry(name='t', action='logger')
    now = utils.timefn()
    assert entry.start in (now-1, now, now+1)


def test_undefined_stop_is_never():
    entry = ScheduleEntry(name='t', action='logger', interval=1)
    assert entry.stop is None
    assert type(entry.get_remaining_times()) is itertools.count


def test_relative_stop():
    # relative stop
    e1 = ScheduleEntry(name='t', start=20, stop=+10, interval=1,
                       relative_stop=True, action='logger')
    assert list(e1.get_remaining_times()) == list(range(20, 30, 1))
    # absolute stop
    e2 = ScheduleEntry(name='t', start=20, stop=10, interval=1,
                       action='logger')
    assert list(e2.get_remaining_times()) == list(range(0))


def test_no_interval():
    e1 = ScheduleEntry(name='t', action='logger')
    remaining_times = list(e1.get_remaining_times())
    assert len(remaining_times) == 1

    times = list(e1.take_until(remaining_times[0]+1000))
    assert len(times) == 1

    # when interval is None, consuming the single task time sets `canceled`
    assert e1.canceled
    assert not list(e1.get_remaining_times())
    assert not list(e1.take_until(remaining_times[0]+1000))

    e2 = ScheduleEntry(name='t', action='logger', start=1)
    remaining_times = list(e2.get_remaining_times())
    assert len(remaining_times) == 1

    times = list(e2.take_until(remaining_times[0]+1000))
    assert len(times) == 1

    # when interval is None, consuming the single task time sets `canceled`
    assert e2.canceled
    assert not list(e2.get_remaining_times())
    assert not list(e2.take_until(remaining_times[0]+1000))


def test_bad_interval_raises():
    with pytest.raises(ValidationError):
        ScheduleEntry(name='t', interval=-1, action='logger').clean_fields()
    with pytest.raises(ValidationError):
        ScheduleEntry(name='t', interval=0, action='logger').clean_fields()
    with pytest.raises(ValidationError):
        ScheduleEntry(name='t', interval=0.1, action='logger').clean_fields()


def test_bad_action_raises():
    with pytest.raises(ValidationError):
        ScheduleEntry(name='t', action='this_doesnt_exist').clean_fields()


def test_bad_name_raises():
    with pytest.raises(ValidationError):  # whitespace
        ScheduleEntry(name='test 1', action='logger').clean_fields()
    with pytest.raises(ValidationError):  # punctuation other than "_-"
        ScheduleEntry(name='test1!', action='logger').clean_fields()

    # ok
    ScheduleEntry(name='_test-Stuff123', action='logger').clean_fields()


@pytest.mark.django_db
def test_non_unique_name_raises():
    ScheduleEntry(name='t', action='logger').save()
    with pytest.raises(ValidationError):
        ScheduleEntry(name='t', action='logger').full_clean()


def test_defaults():
    entry = ScheduleEntry(name='t', action='logger')
    assert entry.priority == DEFAULT_PRIORITY
    # assert entry.action_parameters == {}
    assert entry.start is not None
    assert entry.stop is None
    assert entry.interval is None
    assert entry.relative_stop is False
    assert entry.canceled is False


def test_str():
    str(ScheduleEntry(name='t', action='logger'))
