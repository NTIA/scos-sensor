import pytest
from rest_framework import status

from acquisitions.tests.utils import (get_acquisition_detail,
                                      reverse_acquisition_detail,
                                      simulate_acquisitions)
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response


@pytest.mark.django_db
def test_non_existent_entry(client):
    with pytest.raises(AssertionError):
        get_acquisition_detail(client, 'doesntexist', 1)


@pytest.mark.django_db
def test_non_existent_task_id(client, testclock):
    entry_name = simulate_acquisitions(client, n=1)
    with pytest.raises(AssertionError):
        non_existent_task_id = 2
        get_acquisition_detail(client, entry_name, non_existent_task_id)


@pytest.mark.django_db
def test_get_detail_from_single(client, testclock):
    entry_name = simulate_acquisitions(client, n=1)
    task_id = 1
    acq = get_acquisition_detail(client, entry_name, task_id)
    assert acq['task_id'] == task_id


@pytest.mark.django_db
def test_get_detail_from_multiple(client, testclock):
    entry_name = simulate_acquisitions(client, n=3)
    task_id = 3
    acq = get_acquisition_detail(client, entry_name, task_id)
    assert acq['task_id'] == task_id


@pytest.mark.django_db
def test_delete_single(client, testclock):
    entry_name = simulate_acquisitions(client, n=3)
    task_id_to_delete = 2
    url = reverse_acquisition_detail(entry_name, task_id_to_delete)
    validate_response(client.delete(url), status.HTTP_204_NO_CONTENT)
    validate_response(client.delete(url), status.HTTP_404_NOT_FOUND)
    # other 2 acquisitions should be unaffected
    get_acquisition_detail(client, entry_name, 1)
    get_acquisition_detail(client, entry_name, 3)
