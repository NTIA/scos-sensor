import pytest

from schedule.serializers import ScheduleEntrySerializer


#
# Test serialization
#


@pytest.mark.django_db
def test_minimal_input():
    """A name and action should be the minimum acceptable entry."""
    se = {
        'name': 'test',
        'action': 'logger'
    }
    serializer = ScheduleEntrySerializer(data=se)
    assert serializer.is_valid()



#
# Test deserialization
#
