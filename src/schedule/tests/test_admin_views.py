from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests import TEST_SCHEDULE_ENTRY, TEST_PRIVATE_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule, update_schedule
from sensor.tests.utils import validate_response


HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def test_post_admin_private_schedule(admin_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse('v1:schedule-detail', [entry_name])
    admin_user_respose = admin_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        rjson[k] == v

    assert rjson['is_private'] is True
    validate_response(admin_user_respose, status.HTTP_200_OK)
    assert admin_user_respose.data['is_private'] is True


def test_admin_can_view_all_entries(admin_client, user_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson['name']
    user_url = reverse('v1:schedule-detail', [user_entry_name])

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_url = reverse('v1:schedule-detail', [admin_entry_name])

    response = admin_client.get(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)

    response = admin_client.get(admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_admin_can_delete_all_entries(admin_client, user_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson['name']
    user_url = reverse('v1:schedule-detail', [user_entry_name])

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_url = reverse('v1:schedule-detail', [admin_entry_name])

    response = admin_client.delete(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    response = admin_client.delete(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)

    response = admin_client.delete(admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    response = admin_client.delete(admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_admin_can_modify_all_entries(admin_client, user_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson['name']

    admin_adjust_user_response = update_schedule(
        admin_client, user_entry_name, TEST_PRIVATE_SCHEDULE_ENTRY)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']

    admin_adjust_admin_response = update_schedule(
        admin_client, admin_entry_name, TEST_SCHEDULE_ENTRY)

    validate_response(admin_adjust_user_response, status.HTTP_200_OK)
    assert admin_adjust_user_response.data['is_private'] is True
    validate_response(admin_adjust_admin_response, status.HTTP_200_OK)
    assert admin_adjust_admin_response.data['is_private'] is False
