from rest_framework import status

from schedule.tests import (
    TEST_SCHEDULE_ENTRY,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_ALTERNATE_SCHEDULE_ENTRY)
from schedule.tests.utils import (
    post_schedule,
    update_schedule,
    reverse_detail_url)
from sensor.tests.utils import validate_response


HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def test_user_cant_post_private_schedule(user_client):
    rjson = post_schedule(user_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    assert not rjson['is_private']
    validate_response(user_respose, status.HTTP_200_OK)
    assert not user_respose.data['is_private']


def test_user_can_view_non_private_entries(admin_client, user_client,
                                           alternate_user_client):
    # alternate user schedule entry
    alternate_user_rjson = post_schedule(
        alternate_user_client, TEST_SCHEDULE_ENTRY)
    alternate_user_entry_name = alternate_user_rjson['name']
    alternate_user_entry_url = reverse_detail_url(alternate_user_entry_name)

    user_view_alternate_user_response = user_client.get(
        alternate_user_entry_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_ALTERNATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_entry_url = reverse_detail_url(admin_entry_name)

    user_view_admin_response = user_client.get(admin_entry_url, **HTTPS_KWARG)

    validate_response(
        user_view_alternate_user_response, status.HTTP_200_OK)
    validate_response(user_view_admin_response, status.HTTP_200_OK)


def test_user_cant_view_private_entry(admin_client, user_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)

    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    validate_response(user_respose, status.HTTP_403_FORBIDDEN)


def test_user_can_delete_their_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)

    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_user_cant_delete_any_other_entry(admin_client, user_client,
                                          alternate_user_client):
    # alternate user schedule entry
    alternate_user_rjson = post_schedule(
        alternate_user_client, TEST_SCHEDULE_ENTRY)
    alternate_user_entry_name = alternate_user_rjson['name']
    alternate_user_entry_url = reverse_detail_url(alternate_user_entry_name)

    user_delete_alternate_user_response = user_client.delete(
        alternate_user_entry_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_entry_url = reverse_detail_url(admin_entry_name)

    user_delete_admin_response = user_client.delete(
        admin_entry_url, **HTTPS_KWARG)

    validate_response(
        user_delete_alternate_user_response, status.HTTP_403_FORBIDDEN)
    validate_response(user_delete_admin_response, status.HTTP_403_FORBIDDEN)


def test_user_can_modify_their_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']

    user_adjust_repose = update_schedule(
        user_client, entry_name, TEST_ALTERNATE_SCHEDULE_ENTRY)

    validate_response(user_adjust_repose, status.HTTP_200_OK)
    assert rjson['priority'] == 10
    assert user_adjust_repose.data['priority'] == 5


def test_user_cant_modify_any_other_entry(admin_client, user_client,
                                          alternate_user_client):
    # alternate user schedule entry
    alternate_user_rjson = post_schedule(
        alternate_user_client, TEST_SCHEDULE_ENTRY)
    alternate_user_entry_name = alternate_user_rjson['name']

    user_adjust_alternate_user_response = update_schedule(
        user_client, alternate_user_entry_name, TEST_PRIVATE_SCHEDULE_ENTRY)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']

    user_adjust_admin_response = update_schedule(
        user_client, admin_entry_name, TEST_SCHEDULE_ENTRY)

    validate_response(
        user_adjust_alternate_user_response, status.HTTP_403_FORBIDDEN)
    validate_response(user_adjust_admin_response, status.HTTP_403_FORBIDDEN)
