from rest_framework import status

from acquisitions.tests.utils import (reverse_acquisition_detail,
                                      update_acquisition_detail,
                                      simulate_acquisitions, HTTPS_KWARG)
from sensor.tests.utils import validate_response


def test_admin_can_create_private_acquisition(admin_client, user_client,
                                              test_scheduler):
    private_entry_name = simulate_acquisitions(admin_client, is_private=True)
    private_acq_url = reverse_acquisition_detail(private_entry_name, 1)

    user_response = user_client.get(private_acq_url, **HTTPS_KWARG)

    validate_response(user_response, status.HTTP_403_FORBIDDEN)


def test_admin_can_view_all_acquisitions(admin_client, alt_admin_client,
                                         user_client, test_scheduler):
    # alt admin schedule entry
    alt_admin_entry_name = simulate_acquisitions(
        alt_admin_client, name='alt_admin_single_acq')
    alt_admin_acq_url = reverse_acquisition_detail(alt_admin_entry_name, 1)

    admin_view_alt_admin_response = admin_client.get(alt_admin_acq_url,
                                                     **HTTPS_KWARG)

    # user schedule entry
    user_acq_name = simulate_acquisitions(user_client, name='admin_single_acq')
    user_acq_url = reverse_acquisition_detail(user_acq_name, 1)

    admin_view_user_response = admin_client.get(user_acq_url, **HTTPS_KWARG)

    validate_response(admin_view_alt_admin_response, status.HTTP_200_OK)
    validate_response(admin_view_user_response, status.HTTP_200_OK)


def test_admin_can_view_private_acquisitions(admin_client, alt_admin_client,
                                             test_scheduler):
    private_entry_name = simulate_acquisitions(
        alt_admin_client, is_private=True)
    private_acq_url = reverse_acquisition_detail(private_entry_name, 1)

    response = admin_client.get(private_acq_url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_200_OK)


def test_admin_can_delete_their_acquisition(admin_client, test_scheduler):
    entry_name = simulate_acquisitions(admin_client)
    acq_url = reverse_acquisition_detail(entry_name, 1)

    first_response = admin_client.delete(acq_url, **HTTPS_KWARG)
    second_response = admin_client.delete(acq_url, **HTTPS_KWARG)

    validate_response(first_response, status.HTTP_204_NO_CONTENT)
    validate_response(second_response, status.HTTP_404_NOT_FOUND)


def test_admin_can_delete_other_acquisitions(admin_client, alt_admin_client,
                                             user_client, test_scheduler):
    # alt admin private schedule entry
    alt_admin_entry_name = simulate_acquisitions(
        alt_admin_client, name='alt_admin_single_acq', is_private=True)
    alt_admin_acq_url = reverse_acquisition_detail(alt_admin_entry_name, 1)

    admin_delete_alt_admin_response = admin_client.delete(
        alt_admin_acq_url, **HTTPS_KWARG)

    # user schedule entry
    user_acq_name = simulate_acquisitions(user_client, name='admin_single_acq')
    user_acq_url = reverse_acquisition_detail(user_acq_name, 1)

    admin_delete_user_response = admin_client.delete(user_acq_url,
                                                     **HTTPS_KWARG)

    validate_response(admin_delete_user_response, status.HTTP_204_NO_CONTENT)
    validate_response(admin_delete_alt_admin_response,
                      status.HTTP_204_NO_CONTENT)


def test_admin_cant_modify_their_acquisition(admin_client, test_scheduler):
    entry_name = simulate_acquisitions(admin_client)
    acq_url = reverse_acquisition_detail(entry_name, 1)

    new_acquisition_detail = admin_client.get(acq_url, **HTTPS_KWARG).data

    new_acquisition_detail['task_id'] = 2

    response = update_acquisition_detail(admin_client, entry_name, 1,
                                         new_acquisition_detail)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_user_cant_modify_other_acquisitions(admin_client, alt_admin_client,
                                             user_client, test_scheduler):
    # alt admin schedule entry
    alt_admin_entry_name = simulate_acquisitions(
        alt_admin_client, name='alt_admin_single_acq')
    alt_admin_acq_url = reverse_acquisition_detail(alt_admin_entry_name, 1)

    new_acquisition_detail = user_client.get(alt_admin_acq_url, **HTTPS_KWARG)

    new_acquisition_detail = new_acquisition_detail.data

    new_acquisition_detail['task_id'] = 2

    admin_modify_alt_admin_response = update_acquisition_detail(
        admin_client, alt_admin_entry_name, 1, new_acquisition_detail)

    # user schedule entry
    user_entry_name = simulate_acquisitions(
        user_client, name='admin_single_acq')
    user_acq_url = reverse_acquisition_detail(user_entry_name, 1)

    new_acquisition_detail = admin_client.get(user_acq_url, **HTTPS_KWARG).data

    new_acquisition_detail['task_id'] = 2

    admin_modify_user_response = update_acquisition_detail(
        admin_client, user_entry_name, 1, new_acquisition_detail)

    validate_response(admin_modify_alt_admin_response,
                      status.HTTP_405_METHOD_NOT_ALLOWED)
    validate_response(admin_modify_user_response,
                      status.HTTP_405_METHOD_NOT_ALLOWED)
