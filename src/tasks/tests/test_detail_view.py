import os

from rest_framework import status

from sensor.tests.utils import HTTPS_KWARG, validate_response
from tasks.models import Acquisition, TaskResult
from tasks.tests.utils import (
    create_task_results,
    reverse_result_detail,
    simulate_frequency_fft_acquisitions,
    update_result_detail,
)


def test_admin_can_create_acquisition(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    result_url = reverse_result_detail(entry_name, 1)
    response = admin_client.get(result_url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_200_OK)


def test_admin_can_view_own_result_details(admin_client):
    """A user should be able to view results they create."""
    entry_name = create_task_results(1, admin_client)
    url = reverse_result_detail(entry_name, 1)
    response = admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_admin_can_view_others_result_details(admin_client, alt_admin_client):
    """A user should be able to view results created by others."""
    entry_name = create_task_results(1, admin_client)
    url = reverse_result_detail(entry_name, 1)
    response = alt_admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_user_cannot_view_result_details(admin_client, user_client):
    """A user should be able to view results created by others."""
    entry_name = create_task_results(1, admin_client)
    url = reverse_result_detail(entry_name, 1)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_403_FORBIDDEN)


def test_admin_can_delete_own_results(admin_client, test_scheduler):
    """A user should be able to delete results they own."""
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    result_url = reverse_result_detail(entry_name, 1)

    first_response = admin_client.delete(result_url, **HTTPS_KWARG)
    second_response = admin_client.delete(result_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)


def test_admin_cannot_modify_own_result(admin_client, test_scheduler):
    """Task results are not modifiable."""
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    acq_url = reverse_result_detail(entry_name, 1)

    new_result_detail = admin_client.get(acq_url, **HTTPS_KWARG).data

    new_result_detail["task_id"] = 2

    response = update_result_detail(admin_client, entry_name, 1, new_result_detail)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_admin_cannot_modify_others_results(
    admin_client, alt_admin_client, test_scheduler
):
    # alt user schedule entry
    alt_user_entry_name = simulate_frequency_fft_acquisitions(
        alt_admin_client, name="alt_user_single_acq"
    )
    alt_user_acq_url = reverse_result_detail(alt_user_entry_name, 1)

    new_result_detail = admin_client.get(alt_user_acq_url, **HTTPS_KWARG)

    new_result_detail = new_result_detail.data

    new_result_detail["task_id"] = 2

    user_modify_alt_user_response = update_result_detail(
        admin_client, alt_user_entry_name, 1, new_result_detail
    )

    validate_response(user_modify_alt_user_response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_admin_can_view_all_results(
    admin_client, alt_admin_client, user_client, test_scheduler
):
    # alt admin schedule entry
    alt_admin_entry_name = simulate_frequency_fft_acquisitions(
        alt_admin_client, name="alt_admin_single_acq"
    )
    alt_admin_result_url = reverse_result_detail(alt_admin_entry_name, 1)

    admin_view_alt_admin_response = admin_client.get(
        alt_admin_result_url, **HTTPS_KWARG
    )

    # user schedule entry
    user_result_name = simulate_frequency_fft_acquisitions(
        admin_client, name="admin_single_acq"
    )
    user_result_url = reverse_result_detail(user_result_name, 1)

    admin_view_user_response = admin_client.get(user_result_url, **HTTPS_KWARG)

    validate_response(admin_view_alt_admin_response, status.HTTP_200_OK)
    validate_response(admin_view_user_response, status.HTTP_200_OK)


def test_admin_can_delete_others_results(
    admin_client, alt_admin_client, test_scheduler
):
    # alt admin private schedule entry
    alt_admin_entry_name = simulate_frequency_fft_acquisitions(
        alt_admin_client, name="alt_admin_single_acq"
    )
    alt_admin_result_url = reverse_result_detail(alt_admin_entry_name, 1)

    admin_delete_alt_admin_response = admin_client.delete(
        alt_admin_result_url, **HTTPS_KWARG
    )

    validate_response(admin_delete_alt_admin_response, status.HTTP_204_NO_CONTENT)


def test_user_cannot_delete_others_results(admin_client, user_client, test_scheduler):
    # alt admin private schedule entry
    admin_entry_name = simulate_frequency_fft_acquisitions(
        admin_client, name="alt_admin_single_acq"
    )
    admin_result_url = reverse_result_detail(admin_entry_name, 1)

    user_delete_admin_response = user_client.delete(admin_result_url, **HTTPS_KWARG)

    validate_response(user_delete_admin_response, status.HTTP_403_FORBIDDEN)


def test_deleted_result_deletes_data_file(admin_client, test_scheduler):
    """A user should be able to delete results they own."""
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    # schedule_entry = ScheduleEntry.objects.get(name=entry_name)
    task_result = TaskResult.objects.get(schedule_entry__name=entry_name)
    acquisition = Acquisition.objects.get(task_result__id=task_result.id)
    data_file = acquisition.data.path
    assert os.path.exists(data_file)
    result_url = reverse_result_detail(entry_name, 1)

    first_response = admin_client.delete(result_url, **HTTPS_KWARG)
    second_response = admin_client.delete(result_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)
    assert not os.path.exists(data_file)
