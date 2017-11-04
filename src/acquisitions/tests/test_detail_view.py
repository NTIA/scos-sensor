import pytest
from rest_framework import status

from acquisitions.tests.utils import (
    get_acquisition_detail,
    reverse_acquisition_detail,
    simulate_acquisitions,
    HTTPS_KWARG
)
from sensor.tests.utils import validate_response


def test_non_existent_entry(user_client):
    with pytest.raises(AssertionError):
        get_acquisition_detail(user_client, 'doesntexist', 1)


def test_non_existent_task_id(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=1)
    with pytest.raises(AssertionError):
        non_existent_task_id = 2
        get_acquisition_detail(user_client, entry_name, non_existent_task_id)


def test_get_detail_from_single(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=1)
    task_id = 1
    acq = get_acquisition_detail(user_client, entry_name, task_id)

    assert acq['task_id'] == task_id


def test_get_detail_from_multiple(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=3)
    task_id = 3
    acq = get_acquisition_detail(user_client, entry_name, task_id)

    assert acq['task_id'] == task_id


def test_delete_single(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=3)
    task_id_to_delete = 2
    url = reverse_acquisition_detail(entry_name, task_id_to_delete)

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)

    # other 2 acquisitions should be unaffected
    get_acquisition_detail(user_client, entry_name, 1)
    get_acquisition_detail(user_client, entry_name, 3)
