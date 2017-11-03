import time
import pytest
from rest_framework import status

from acquisitions.tests.utils import (
    get_acquisition_list, reverse_acquisition_detail, reverse_acquisition_list,
    simulate_acquisitions, HTTPS_KWARG)
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response

@pytest.mark.django_db
def test_non_existent_entry(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    with pytest.raises(AssertionError):
        get_acquisition_list(client, 'doesntexist')


@pytest.mark.django_db
def test_entry_with_no_acquisition_response(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    entry = post_schedule(client, TEST_SCHEDULE_ENTRY)

    with pytest.raises(AssertionError):
        assert get_acquisition_list(client, entry['name'])


@pytest.mark.django_db
def test_single_acquisition_response(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    entry_name = simulate_acquisitions(client, n=1)
    acquisition, = get_acquisition_list(client, entry_name)
    task_id = 1
    expected_url = reverse_acquisition_detail(entry_name, task_id)

    assert acquisition['url'] == expected_url
    assert acquisition['task_id'] == task_id


@pytest.mark.django_db
def test_multiple_acquisition_response(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    entry_name = simulate_acquisitions(client, n=3)
    acquisitions = get_acquisition_list(client, entry_name)

    assert len(acquisitions) == 3

    for i, acq in enumerate(acquisitions, start=1):
        expected_url = reverse_acquisition_detail(entry_name, i)

        assert acq['url'] == expected_url
        assert acq['task_id'] == i


@pytest.mark.django_db
def test_delete_list(client, testclock, test_user):
    client.login(username=test_user.username, password=test_user.password)

    entry_name = simulate_acquisitions(client, n=3)
    url = reverse_acquisition_list(entry_name)

    validate_response(
        client.delete(url, **HTTPS_KWARG), status.HTTP_204_NO_CONTENT)
    validate_response(
        client.delete(url, **HTTPS_KWARG), status.HTTP_404_NOT_FOUND)
