from rest_framework import status

from acquisitions.tests.utils import (
    reverse_acquisition_detail,
    update_acquisition_detail,
    simulate_acquisitions,
    HTTPS_KWARG
)
from sensor.tests.utils import validate_response


def test_user_can_create_nonprivate_acquisition(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client)
    acq_url = reverse_acquisition_detail(entry_name, 1)
    response = user_client.get(acq_url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_200_OK)


def test_user_cant_create_private_acquisition(user_client, alt_user_client,
                                              test_scheduler):
    # The alt user attempts to create a private acquisition.
    entry_name = simulate_acquisitions(alt_user_client, is_private=True)
    acq_url = reverse_acquisition_detail(entry_name, 1)

    # The user attempts to GET the acquisition that the alt user created.
    response = user_client.get(acq_url, **HTTPS_KWARG)

    # The user successfully GETs the acquistion that the alt user
    # created; meaning that the acquisition was not, in fact, private.
    validate_response(response, status.HTTP_200_OK)


def test_user_can_view_other_nonprivate_acquisitions(admin_client, user_client,
                                                     alt_user_client,
                                                     test_scheduler):
    # alt user schedule entry
    alt_user_entry_name = simulate_acquisitions(
        alt_user_client, name='alt_user_single_acq')
    alt_user_acq_url = reverse_acquisition_detail(alt_user_entry_name, 1)

    user_view_alt_user_response = user_client.get(
        alt_user_acq_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_acq_name = simulate_acquisitions(
        admin_client, name='admin_single_acq')
    admin_acq_url = reverse_acquisition_detail(admin_acq_name, 1)

    user_view_admin_response = user_client.get(admin_acq_url, **HTTPS_KWARG)

    validate_response(user_view_alt_user_response, status.HTTP_200_OK)
    validate_response(user_view_admin_response, status.HTTP_200_OK)


def test_user_cant_view_private_acquisitions(admin_client, user_client,
                                             test_scheduler):
    private_entry_name = simulate_acquisitions(admin_client, is_private=True)
    private_acq_url = reverse_acquisition_detail(private_entry_name, 1)

    response = user_client.get(private_acq_url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_403_FORBIDDEN)


def test_user_can_delete_their_acquisition(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client)
    acq_url = reverse_acquisition_detail(entry_name, 1)

    first_response = user_client.delete(acq_url, **HTTPS_KWARG)
    second_response = user_client.delete(acq_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)


def test_user_cant_delete_other_acquisitions(admin_client, user_client,
                                             alt_user_client,
                                             test_scheduler):
    # alt user schedule entry
    alt_user_entry_name = simulate_acquisitions(
        alt_user_client, name='alt_user_single_acq')
    alt_user_acq_url = reverse_acquisition_detail(alt_user_entry_name, 1)

    user_delete_alt_user_response = user_client.delete(
        alt_user_acq_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_acq_name = simulate_acquisitions(
        admin_client, name='admin_single_acq')
    admin_acq_url = reverse_acquisition_detail(admin_acq_name, 1)

    user_delete_admin_response = user_client.delete(
        admin_acq_url, **HTTPS_KWARG)

    validate_response(user_delete_admin_response, status.HTTP_403_FORBIDDEN)
    validate_response(
        user_delete_alt_user_response, status.HTTP_403_FORBIDDEN)


def test_user_cant_modify_their_acquisition(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client)
    acq_url = reverse_acquisition_detail(entry_name, 1)

    new_acquisition_detail = user_client.get(acq_url, **HTTPS_KWARG).data

    new_acquisition_detail['task_id'] = 2

    response = update_acquisition_detail(
        user_client, entry_name, 1, new_acquisition_detail)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_user_cant_modify_other_acquisitions(admin_client, user_client,
                                             alt_user_client,
                                             test_scheduler):
    # alt user schedule entry
    alt_user_entry_name = simulate_acquisitions(
        alt_user_client, name='alt_user_single_acq')
    alt_user_acq_url = reverse_acquisition_detail(alt_user_entry_name, 1)

    new_acquisition_detail = user_client.get(alt_user_acq_url, **HTTPS_KWARG)

    new_acquisition_detail = new_acquisition_detail.data

    new_acquisition_detail['task_id'] = 2

    user_modify_alt_user_response = update_acquisition_detail(
        user_client, alt_user_entry_name, 1, new_acquisition_detail)

    # admin user schedule entry
    admin_entry_name = simulate_acquisitions(
        admin_client, name='admin_single_acq')
    admin_acq_url = reverse_acquisition_detail(admin_entry_name, 1)

    new_acquisition_detail = user_client.get(admin_acq_url, **HTTPS_KWARG).data

    new_acquisition_detail['task_id'] = 2

    user_modify_admin_response = update_acquisition_detail(
        user_client, admin_entry_name, 1, new_acquisition_detail)

    validate_response(user_modify_alt_user_response, status.HTTP_403_FORBIDDEN)
    validate_response(user_modify_admin_response, status.HTTP_403_FORBIDDEN)
