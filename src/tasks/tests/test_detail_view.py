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


def test_user_can_create_nonprivate_acquisition(user_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(user_client)
    result_url = reverse_result_detail(entry_name, 1)
    response = user_client.get(result_url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_200_OK)


def test_user_cant_create_private_acquisition(
    user_client, alt_user_client, test_scheduler
):
    # The alt user attempts to create a private acquisition.
    entry_name = simulate_frequency_fft_acquisitions(alt_user_client, is_private=True)
    result_url = reverse_result_detail(entry_name, 1)

    # The user attempts to GET the acquisition that the alt user created.
    response = user_client.get(result_url, **HTTPS_KWARG)

    # The user successfully GETs the acquistion that the alt user
    # created; meaning that the acquisition was not, in fact, private.
    validate_response(response, status.HTTP_200_OK)


def test_user_can_view_own_result_details(user_client):
    """A user should be able to view results they create."""
    entry_name = create_task_results(1, user_client)
    url = reverse_result_detail(entry_name, 1)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_user_can_view_others_result_details(user_client, alt_user_client):
    """A user should be able to view results created by others."""
    entry_name = create_task_results(1, user_client)
    url = reverse_result_detail(entry_name, 1)
    response = alt_user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_user_cannot_view_private_result_details(
    user_client, admin_client, test_scheduler
):
    """A user should not be able to view the result of a private task."""
    entry_name = simulate_frequency_fft_acquisitions(admin_client, is_private=True)
    task_id = 1
    url = reverse_result_detail(entry_name, task_id)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_403_FORBIDDEN)


def test_user_can_delete_own_results(user_client, test_scheduler):
    """A user should be able to delete results they own."""
    entry_name = simulate_frequency_fft_acquisitions(user_client)
    result_url = reverse_result_detail(entry_name, 1)

    first_response = user_client.delete(result_url, **HTTPS_KWARG)
    second_response = user_client.delete(result_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)


def test_user_cant_delete_others_results(
    admin_client, user_client, alt_user_client, test_scheduler
):
    # alt user schedule entry
    alt_user_entry_name = simulate_frequency_fft_acquisitions(
        alt_user_client, name="alt_user_single_acq"
    )
    alt_user_result_url = reverse_result_detail(alt_user_entry_name, 1)

    user_delete_alt_user_response = user_client.delete(
        alt_user_result_url, **HTTPS_KWARG
    )

    # admin user schedule entry
    admin_result_name = simulate_frequency_fft_acquisitions(
        admin_client, name="admin_single_acq"
    )
    admin_result_url = reverse_result_detail(admin_result_name, 1)

    user_delete_admin_response = user_client.delete(admin_result_url, **HTTPS_KWARG)

    validate_response(user_delete_admin_response, status.HTTP_403_FORBIDDEN)
    validate_response(user_delete_alt_user_response, status.HTTP_403_FORBIDDEN)


def test_user_cant_modify_own_result(user_client, test_scheduler):
    """Task results are not modifiable."""
    entry_name = simulate_frequency_fft_acquisitions(user_client)
    acq_url = reverse_result_detail(entry_name, 1)

    new_result_detail = user_client.get(acq_url, **HTTPS_KWARG).data

    new_result_detail["task_id"] = 2

    response = update_result_detail(user_client, entry_name, 1, new_result_detail)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_user_cant_modify_others_results(
    admin_client, user_client, alt_user_client, test_scheduler
):
    # alt user schedule entry
    alt_user_entry_name = simulate_frequency_fft_acquisitions(
        alt_user_client, name="alt_user_single_acq"
    )
    alt_user_acq_url = reverse_result_detail(alt_user_entry_name, 1)

    new_result_detail = user_client.get(alt_user_acq_url, **HTTPS_KWARG)

    new_result_detail = new_result_detail.data

    new_result_detail["task_id"] = 2

    user_modify_alt_user_response = update_result_detail(
        user_client, alt_user_entry_name, 1, new_result_detail
    )

    # admin user schedule entry
    admin_entry_name = simulate_frequency_fft_acquisitions(
        admin_client, name="admin_single_acq"
    )
    admin_acq_url = reverse_result_detail(admin_entry_name, 1)

    new_result_detail = user_client.get(admin_acq_url, **HTTPS_KWARG).data

    new_result_detail["task_id"] = 2

    user_modify_admin_response = update_result_detail(
        user_client, admin_entry_name, 1, new_result_detail
    )

    validate_response(user_modify_alt_user_response, status.HTTP_403_FORBIDDEN)
    validate_response(user_modify_admin_response, status.HTTP_403_FORBIDDEN)


def test_admin_can_create_private_results(admin_client, user_client, test_scheduler):
    private_entry_name = simulate_frequency_fft_acquisitions(
        admin_client, is_private=True
    )
    private_result_url = reverse_result_detail(private_entry_name, 1)
    user_response = user_client.get(private_result_url, **HTTPS_KWARG)
    validate_response(user_response, status.HTTP_403_FORBIDDEN)


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
        user_client, name="admin_single_acq"
    )
    user_result_url = reverse_result_detail(user_result_name, 1)

    admin_view_user_response = admin_client.get(user_result_url, **HTTPS_KWARG)

    validate_response(admin_view_alt_admin_response, status.HTTP_200_OK)
    validate_response(admin_view_user_response, status.HTTP_200_OK)


def test_admin_can_view_private_results(admin_client, alt_admin_client, test_scheduler):
    private_entry_name = simulate_frequency_fft_acquisitions(
        alt_admin_client, is_private=True
    )
    private_result_url = reverse_result_detail(private_entry_name, 1)
    response = admin_client.get(private_result_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_admin_can_delete_own_results(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    result_url = reverse_result_detail(entry_name, 1)

    first_response = admin_client.delete(result_url, **HTTPS_KWARG)
    second_response = admin_client.delete(result_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)


def test_admin_can_delete_others_results(
    admin_client, alt_admin_client, user_client, test_scheduler
):
    # alt admin private schedule entry
    alt_admin_entry_name = simulate_frequency_fft_acquisitions(
        alt_admin_client, name="alt_admin_single_acq", is_private=True
    )
    alt_admin_result_url = reverse_result_detail(alt_admin_entry_name, 1)

    admin_delete_alt_admin_response = admin_client.delete(
        alt_admin_result_url, **HTTPS_KWARG
    )

    # user schedule entry
    user_result_name = simulate_frequency_fft_acquisitions(
        user_client, name="admin_single_acq"
    )
    user_result_url = reverse_result_detail(user_result_name, 1)

    admin_delete_user_response = admin_client.delete(user_result_url, **HTTPS_KWARG)

    validate_response(admin_delete_user_response, status.HTTP_204_NO_CONTENT)
    validate_response(admin_delete_alt_admin_response, status.HTTP_204_NO_CONTENT)


def test_admin_cant_modify_own_results(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    result_url = reverse_result_detail(entry_name, 1)

    new_result_detail = admin_client.get(result_url, **HTTPS_KWARG).data

    new_result_detail["task_id"] = 2

    response = update_result_detail(admin_client, entry_name, 1, new_result_detail)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_deleted_result_deletes_data_file(user_client, test_scheduler):
    """A user should be able to delete results they own."""
    entry_name = simulate_frequency_fft_acquisitions(user_client)
    # schedule_entry = ScheduleEntry.objects.get(name=entry_name)
    task_result = TaskResult.objects.get(schedule_entry__name=entry_name)
    acquisition = Acquisition.objects.get(task_result__id=task_result.id)
    data_file = acquisition.data.path
    assert os.path.exists(data_file)
    result_url = reverse_result_detail(entry_name, 1)

    first_response = user_client.delete(result_url, **HTTPS_KWARG)
    second_response = user_client.delete(result_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)
    assert not os.path.exists(data_file)
