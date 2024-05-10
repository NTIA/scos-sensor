import pytest

from schedule.serializers import ScheduleEntrySerializer
from sensor.utils import parse_datetime_str

from .utils import post_schedule

#
# Test deserialization
#


# Test that valid user input is valid
@pytest.mark.django_db
@pytest.mark.parametrize(
    "entry_json",
    [
        # A name and action should be the minimum acceptable entry
        # i.e., (one-shot, ASAP)
        {"name": "test", "action": "test_monitor_sigan"},
        # Stop 10 seconds after starting, start ASAP
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 10},
        # Min integer interval ok
        {"name": "test", "action": "test_monitor_sigan", "interval": 10},
        # Max priority ok
        {"name": "test", "action": "test_monitor_sigan", "priority": 19},
        # Min user priority ok
        {"name": "test", "action": "test_monitor_sigan", "priority": 0},
        # Stop 10 seconds after starting; start at absolute time
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25Z",
            "relative_stop": 10,
        },
        # Start and stop at absolute time; equivalent to above
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25Z",
            "absolute_stop": "2018-03-16T17:12:35Z",
        },
        # 'stop' and 'absolute_stop' are synonyms
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "stop": "2018-03-16T17:12:35.0Z",
        },
        # Subseconds are optional
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
        },
        # Sensor is timezone-aware
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-22T13:53:25-06:00",
        },
        # All non-boolean, non-required fields accepts null to mean not defined
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": None,
            "absolute_stop": None,
            "relative_stop": None,
            "priority": None,
            "start": None,
            "start": None,
            "interval": None,
            "callback_url": None,
        },
        # Explicit validate_only is valid
        {"name": "test", "action": "test_monitor_sigan", "validate_only": False},
    ],
)
def test_valid_user_entries(entry_json, user):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert serializer.is_valid()
    serializer.save(owner=user)  # if input is valid, model should accept it


# Test that valid admin input is valid
@pytest.mark.django_db
@pytest.mark.parametrize(
    "entry_json",
    [
        # A name and action should be the minimum acceptable entry
        # i.e., (one-shot, ASAP)
        {"name": "test", "action": "test_monitor_sigan"},
        # Stop 10 seconds after starting, start ASAP
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 10},
        # Min integer interval ok
        {"name": "test", "action": "test_monitor_sigan", "interval": 10},
        # Max priority ok
        {"name": "test", "action": "test_monitor_sigan", "priority": 19},
        # Min admin priority ok
        {"name": "test", "action": "test_monitor_sigan", "priority": -20},
        # Stop 10 seconds after starting; start at absolute time
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25Z",
            "relative_stop": 10,
        },
        # Start and stop at absolute time; equivalent to above
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25Z",
            "absolute_stop": "2018-03-16T17:12:35Z",
        },
        # 'stop' and 'absolute_stop' are synonyms
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "stop": "2018-03-16T17:12:35.0Z",
        },
        # Subseconds are optional
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
        },
        # Sensor is timezone-aware
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-22T13:53:25-06:00",
        },
        # All non-boolean, non-required fields accepts null to mean not defined
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": None,
            "absolute_stop": None,
            "relative_stop": None,
            "priority": None,
            "start": None,
            "start": None,
            "interval": None,
            "callback_url": None,
        },
        # Explicit validate_only is valid
        {"name": "test", "action": "test_monitor_sigan", "validate_only": False},
        # Admin can create private entries
        {"name": "test", "action": "test_monitor_sigan"},
    ],
)
def test_valid_admin_entries(entry_json, user):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert serializer.is_valid()
    serializer.save(owner=user)  # if input is valid, model should accept it


# Test that invalid user input is invalid
@pytest.mark.django_db
@pytest.mark.parametrize(
    "entry_json",
    [
        # name is a required field
        {"action": "test_monitor_sigan"},
        # action is a required field
        {"name": "test"},
        # non-integer priority
        {"name": "test", "action": "test_monitor_sigan", "priority": 3.14},
        # priority greater than max (19)
        {"name": "test", "action": "test_monitor_sigan", "priority": 20},
        # non-integer interval
        {"name": "test", "action": "test_monitor_sigan", "interval": 3.14},
        # zero interval
        {"name": "test", "action": "test_monitor_sigan", "interval": 0},
        # negative interval
        {"name": "test", "action": "test_monitor_sigan", "interval": -1},
        # can't interpret both absolute and relative stop
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25.0Z",
            "absolute_stop": "2018-03-16T17:12:35.0Z",
            "relative_stop": 10,
        },
        # 0 relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 0},
        # negative relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": -10},
        # non-integer relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 3.14},
        # stop is before start
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
            "stop": "2018-03-16T17:12:30Z",
        },
        # stop is same as start
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
            "stop": "2018-03-16T17:12:35Z",
        },
    ],
)
def test_invalid_user_entries(entry_json):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert not serializer.is_valid()


# Test that invalid admin input is invalid
@pytest.mark.django_db
@pytest.mark.parametrize(
    "entry_json",
    [
        # name is a required field
        {"action": "test_monitor_sigan"},
        # action is a required field
        {"name": "test"},
        # non-integer priority
        {"name": "test", "action": "test_monitor_sigan", "priority": 3.14},
        # priority less than min (for admin)
        {"name": "test", "action": "test_monitor_sigan", "priority": -21},
        # priority greater than max (19)
        {"name": "test", "action": "test_monitor_sigan", "priority": 20},
        # non-integer interval
        {"name": "test", "action": "test_monitor_sigan", "interval": 3.14},
        # zero interval
        {"name": "test", "action": "test_monitor_sigan", "interval": 0},
        # negative interval
        {"name": "test", "action": "test_monitor_sigan", "interval": -1},
        # can't interpret both absolute and relative stop
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:25.0Z",
            "absolute_stop": "2018-03-16T17:12:35.0Z",
            "relative_stop": 10,
        },
        # 0 relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 0},
        # negative relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": -10},
        # non-integer relative_stop
        {"name": "test", "action": "test_monitor_sigan", "relative_stop": 3.14},
        # stop is before start
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
            "stop": "2018-03-16T17:12:30Z",
        },
        # stop is same as start
        {
            "name": "test",
            "action": "test_monitor_sigan",
            "start": "2018-03-16T17:12:35Z",
            "stop": "2018-03-16T17:12:35Z",
        },
    ],
)
def test_invalid_admin_entries(entry_json):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert not serializer.is_valid()


#
# Test serialization
#


def test_serialized_fields(admin_client):
    """Certain fields on the schedule entry model should be serialized."""
    rjson = post_schedule(
        admin_client, {"name": "test", "action": "test_monitor_sigan"}
    )

    # nullable fields
    assert "interval" in rjson
    assert "callback_url" in rjson
    # non-nullable fields
    assert rjson["name"]
    assert rjson["action"]
    assert rjson["priority"] is not None  # potentially 0
    assert rjson["next_task_id"]
    # nullable datetimes
    assert rjson["start"] is None or parse_datetime_str(rjson["start"])
    assert rjson["stop"] is None or parse_datetime_str(rjson["stop"])
    # datetimes
    assert parse_datetime_str(rjson["created"])
    assert parse_datetime_str(rjson["modified"])
    assert parse_datetime_str(rjson["next_task_time"])
    # booleans
    assert rjson["is_active"] in {True, False}
    # links
    assert rjson["self"]
    assert rjson["owner"]
    assert rjson["task_results"]


def test_non_serialized_fields(admin_client):
    """Certain fields on the schedule entry model should not be serialized."""
    rjson = post_schedule(
        admin_client, {"name": "test", "action": "test_monitor_sigan"}
    )

    assert "relative_stop" not in rjson
