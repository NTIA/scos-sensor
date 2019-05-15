import pytest
from rest_framework import status

from acquisitions.tests.utils import (
    get_acquisition_list, reverse_acquisition_detail, reverse_acquisition_list,
    simulate_acquisitions)
from schedule.tests.utils import post_schedule, TEST_SCHEDULE_ENTRY
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_non_existent_entry(user_client, test_scheduler):
    with pytest.raises(AssertionError):
        get_acquisition_list(user_client, 'doesntexist')


@pytest.mark.django_db
def test_entry_with_no_acquisition_response(user_client, test_scheduler):
    entry = post_schedule(user_client, TEST_SCHEDULE_ENTRY)

    with pytest.raises(AssertionError):
        assert get_acquisition_list(user_client, entry['name'])


@pytest.mark.django_db
def test_single_acquisition_response(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, n=1)
    acquisition, = get_acquisition_list(user_client, entry_name)
    task_id = 1
    expected_url = reverse_acquisition_detail(entry_name, task_id)

    assert acquisition['self'] == expected_url
    assert acquisition['task_id'] == task_id


@pytest.mark.django_db
def test_multiple_acquisition_response(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, n=3)
    acquisitions = get_acquisition_list(user_client, entry_name)
    assert len(acquisitions) == 3

    for i, acq in enumerate(acquisitions, start=1):
        expected_url = reverse_acquisition_detail(entry_name, i)
        assert acq['self'] == expected_url
        assert acq['task_id'] == i


@pytest.mark.django_db
def test_delete_list(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, n=3)
    url = reverse_acquisition_list(entry_name)

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)
