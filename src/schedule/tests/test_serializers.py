import pytest

from schedule.serializers import ScheduleEntrySerializer
from sensor.utils import parse_datetime_str

from .utils import post_schedule


#
# Test deserialization
#


# Test that valid input is valid
@pytest.mark.django_db
@pytest.mark.parametrize('entry_json', [
    # a name and action should be the minimum acceptable entry (one-shot, ASAP)
    {'name': 'test', 'action': 'logger'},
    # stop 10 seconds after starting, start ASAP
    {'name': 'test', 'action': 'logger', 'relative_stop': 10},
    # positive integer interval ok
    {'name': 'test', 'action': 'logger', 'interval': 10},
    # positive integer priority ok
    {'name': 'test', 'action': 'logger', 'priority': 1},
    # zero integer priority ok
    {'name': 'test', 'action': 'logger', 'priority': 0},
    # negative integer priority ok
    {'name': 'test', 'action': 'logger', 'priority': -1},
    # stop 10 seconds after starting; start at absolute time
    {
        'name': 'test',
        'action': 'logger',
        'start': '2018-03-16T17:12:25Z',
        'relative_stop': 10,
    },
    # start and stop at absolute time; equivalent to above
    {
        'name': 'test',
        'action': 'logger',
        'start': '2018-03-16T17:12:25Z',
        'absolute_stop': '2018-03-16T17:12:35Z',
    },
    # 'stop' and 'absolute_stop' are synonyms
    {'name': 'test', 'action': 'logger', 'stop': '2018-03-16T17:12:35.0Z'},

])
def test_valid_entries(entry_json):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert serializer.is_valid()


# Test that invalid input is invalid
@pytest.mark.django_db
@pytest.mark.parametrize('entry_json', [
    # name is a required field
    {'action': 'logger'},
    # action is a required field
    {'name': 'test'},
    # non-integer priority
    {'name': 'test', 'action': 'logger', 'priority': 3.14},
    # non-integer interval
    {'name': 'test', 'action': 'logger', 'interval': 3.14},
    # zero interval
    {'name': 'test', 'action': 'logger', 'interval': 0},
    # negative interval
    {'name': 'test', 'action': 'logger', 'interval': -1},
    # can't interpret both absolute and relative stop
    {
        'name': 'test',
        'action': 'logger',
        'start': '2018-03-16T17:12:25.0Z',
        'absolute_stop': '2018-03-16T17:12:35.0Z',
        'relative_stop': 10,
    },
    # 0 relative_stop
    {'name': 'test', 'action': 'logger', 'relative_stop': 0},
    # negative relative_stop
    {'name': 'test', 'action': 'logger', 'relative_stop': -10},
    # non-integer relative_stop
    {'name': 'test', 'action': 'logger', 'relative_stop': 3.14},
])
def test_invalid_entries(entry_json):
    serializer = ScheduleEntrySerializer(data=entry_json)
    assert not serializer.is_valid()


#
# Test serialization
#


def test_serialized_fields(user_client):
    """Certain fields on the schedule entry model should be serialized."""
    rjson = post_schedule(user_client, {'name': 'test', 'action': 'logger'})

    # nullable fields
    assert 'interval' in rjson
    assert 'callback_url' in rjson
    # non-nullable fields
    assert rjson['name']
    assert rjson['action']
    assert rjson['priority'] is not None  # potentially 0
    assert rjson['next_task_id']
    # nullable datetimes
    assert rjson['start'] is None or parse_datetime_str(rjson['start'])
    assert rjson['stop'] is None or parse_datetime_str(rjson['stop'])
    # datetimes
    assert parse_datetime_str(rjson['created'])
    assert parse_datetime_str(rjson['modified'])
    assert parse_datetime_str(rjson['next_task_time'])
    # booleans
    assert rjson['is_active'] in {True, False}
    assert rjson['is_private'] in {True, False}
    # links
    assert rjson['url']
    assert rjson['owner']
    assert rjson['results']
    assert rjson['acquisitions']


def test_non_serialized_fields(user_client):
    """Certain fields on the schedule entry model should not be serialized."""
    rjson = post_schedule(user_client, {'name': 'test', 'action': 'logger'})

    assert 'relative_stop' not in rjson
