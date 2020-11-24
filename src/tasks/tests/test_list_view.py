import os

import pytest
from rest_framework import status

from sensor.tests.utils import HTTPS_KWARG, validate_response
from tasks.models import Acquisition, TaskResult
from tasks.tests.utils import (
    create_task_results,
    get_result_list,
    reverse_result_detail,
    reverse_result_list,
    simulate_frequency_fft_acquisitions,
)


def test_non_existent_entry(user_client):
    with pytest.raises(AssertionError):
        get_result_list(user_client, "doesntexist")


@pytest.mark.django_db
def test_single_result_response(user_client):
    entry_name = create_task_results(1, user_client)
    (result,) = get_result_list(user_client, entry_name)
    task_id = 1
    expected_url = reverse_result_detail(entry_name, task_id)
    assert result["self"] == expected_url
    assert result["task_id"] == task_id


@pytest.mark.django_db
def test_multiple_result_response(user_client, test_scheduler):
    entry_name = create_task_results(3, user_client)
    results = get_result_list(user_client, entry_name)
    assert len(results) == 3

    for i, acq in enumerate(results, start=1):
        expected_url = reverse_result_detail(entry_name, i)
        assert acq["self"] == expected_url
        assert acq["task_id"] == i


def test_private_entry_results_list_is_private(
    admin_client, user_client, test_scheduler
):
    entry_name = simulate_frequency_fft_acquisitions(admin_client, is_private=True)
    url = reverse_result_list(entry_name)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_delete_list(user_client):
    # If result doesn't exist, expect 404
    url = reverse_result_list("doesntexist")
    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)

    # If result does exist, expect 204
    entry_name = create_task_results(1, user_client)

    url = reverse_result_list(entry_name)
    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)


def test_delete_list_data_files_deleted(user_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(user_client)
    task_result = TaskResult.objects.get(schedule_entry__name=entry_name)
    acquisition = Acquisition.objects.get(task_result__id=task_result.id)
    data_file = acquisition.data.path
    assert os.path.exists(data_file)
    url = reverse_result_list(entry_name)
    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    assert not os.path.exists(data_file)
