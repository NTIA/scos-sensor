from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_SCHEDULE_ENTRY,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_ALTERNATE_SCHEDULE_ENTRY,
    post_schedule,
    update_schedule,
    reverse_detail_url
)
from sensor import V1
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_user_cannot_post_private_schedule(user_client):
    """Unpriveleged users should not be able to create private entries."""
    rjson = post_schedule(user_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse_detail_url(entry_name)
    response = user_client.get(url, **HTTPS_KWARG)
    assert not rjson['is_private']
    validate_response(response, status.HTTP_200_OK)
    assert not response.data['is_private']


def test_user_can_view_non_private_user_entries(user_client, alt_user_client):
    # alt user schedule entry
    alt_user_rjson = post_schedule(alt_user_client, TEST_SCHEDULE_ENTRY)
    alt_user_entry_name = alt_user_rjson['name']
    alt_user_entry_url = reverse_detail_url(alt_user_entry_name)
    response = user_client.get(alt_user_entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_user_can_view_non_private_admin_entries(admin_client, user_client):
    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_ALTERNATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_entry_url = reverse_detail_url(admin_entry_name)
    response = user_client.get(admin_entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_user_cannot_view_private_entry_in_list(admin_client, user_client):
    post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    url = reverse('schedule-list', kwargs=V1)
    response = user_client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_200_OK)
    assert rjson == EMPTY_SCHEDULE_RESPONSE


def test_user_cannot_view_private_entry_details(admin_client, user_client):
    """A user attempting to access a private entry should receive 404."""
    # Private indicates admin wants users to be unaware that the entry exists
    # on the system, hence 404 vs 403 (FORBIDDEN).
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse_detail_url(entry_name)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_user_can_delete_their_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)

    # First attempt to delete should return 204
    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    # Second attempt to delete should return 404
    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_user_cannot_delete_any_other_entry(admin_client, user_client,
                                            alt_user_client):
    # alt user schedule entry
    alt_user_rjson = post_schedule(alt_user_client, TEST_SCHEDULE_ENTRY)
    alt_user_entry_name = alt_user_rjson['name']
    alt_user_entry_url = reverse_detail_url(alt_user_entry_name)

    user_delete_alt_user_response = user_client.delete(
        alt_user_entry_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']
    admin_entry_url = reverse_detail_url(admin_entry_name)

    user_delete_admin_response = user_client.delete(
        admin_entry_url, **HTTPS_KWARG)

    validate_response(user_delete_alt_user_response, status.HTTP_403_FORBIDDEN)
    # Admin's entry is private, hence 404 instead of 403
    validate_response(user_delete_admin_response, status.HTTP_404_NOT_FOUND)


def test_user_can_modify_their_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']

    user_adjust_response = update_schedule(
        user_client, entry_name, TEST_ALTERNATE_SCHEDULE_ENTRY)

    validate_response(user_adjust_response, status.HTTP_200_OK)
    assert rjson['priority'] == 10
    assert user_adjust_response.data['priority'] == 5


def test_user_cannot_modify_any_other_entry(admin_client, user_client,
                                            alt_user_client):
    # alt user schedule entry
    alt_user_rjson = post_schedule(alt_user_client, TEST_SCHEDULE_ENTRY)
    alt_user_entry_name = alt_user_rjson['name']

    user_adjust_alt_user_response = update_schedule(
        user_client, alt_user_entry_name, TEST_PRIVATE_SCHEDULE_ENTRY)

    # admin user schedule entry
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson['name']

    user_adjust_admin_response = update_schedule(
        user_client, admin_entry_name, TEST_SCHEDULE_ENTRY)

    validate_response(
        user_adjust_alt_user_response, status.HTTP_403_FORBIDDEN)
    # Admin's entry is private, hence 404 instead of 403
    validate_response(user_adjust_admin_response, status.HTTP_404_NOT_FOUND)
