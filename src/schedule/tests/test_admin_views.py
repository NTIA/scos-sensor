from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_ALTERNATE_SCHEDULE_ENTRY,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_SCHEDULE_ENTRY,
    post_schedule,
    reverse_detail_url,
    update_schedule,
)
from sensor import V1
from sensor.tests.utils import HTTPS_KWARG, validate_response


def test_admin_can_view_entry_in_list(admin_client):
    post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    url = reverse("schedule-list", kwargs=V1)
    response = admin_client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_200_OK)
    assert rjson != EMPTY_SCHEDULE_RESPONSE


def test_admin_can_view_all_entries(admin_client, alt_admin_client):
    # alt admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]
    kws = {"pk": alt_admin_entry_name}
    kws.update(V1)
    alt_admin_url = reverse("schedule-detail", kwargs=kws)

    response = admin_client.get(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_admin_can_delete_all_entries(admin_client, alt_admin_client):

    # admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]
    kws = {"pk": alt_admin_entry_name}
    kws.update(V1)
    alt_admin_url = reverse("schedule-detail", kwargs=kws)

    response = admin_client.delete(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    response = admin_client.delete(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_admin_can_modify_all_entries(admin_client, alt_admin_client):
    # admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]

    admin_adjust_alt_admin_response = update_schedule(
        admin_client, alt_admin_entry_name, TEST_SCHEDULE_ENTRY
    )

    validate_response(admin_adjust_alt_admin_response, status.HTTP_200_OK)


def test_admin_can_use_negative_priority(admin_client):
    hipri = TEST_PRIVATE_SCHEDULE_ENTRY.copy()
    hipri["priority"] = -20
    rjson = post_schedule(admin_client, hipri)
    entry_name = rjson["name"]
    kws = {"pk": entry_name}
    kws.update(V1)
    entry_url = reverse("schedule-detail", kwargs=kws)
    admin_user_respose = admin_client.get(entry_url, **HTTPS_KWARG)

    assert rjson["priority"] == -20
    validate_response(admin_user_respose, status.HTTP_200_OK)


def test_admin_can_delete_their_entry(admin_client):
    rjson = post_schedule(admin_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson["name"]
    entry_url = reverse_detail_url(entry_name)

    # First attempt to delete should return 204
    response = admin_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    # Second attempt to delete should return 404
    response = admin_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_admin_can_modify_their_entry(admin_client):
    rjson = post_schedule(admin_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson["name"]

    user_adjust_response = update_schedule(
        admin_client, entry_name, TEST_ALTERNATE_SCHEDULE_ENTRY
    )

    validate_response(user_adjust_response, status.HTTP_200_OK)
    assert rjson["priority"] == 10
    assert user_adjust_response.data["priority"] == 5


def test_validate_only_does_not_modify_schedule_with_good_entry(admin_client):
    """A good entry with validate_only should return 200 only."""
    # Ensure that a 200 "OK" is returned from the validator
    entry = TEST_SCHEDULE_ENTRY.copy()
    entry["validate_only"] = True
    expected_status = status.HTTP_204_NO_CONTENT
    post_schedule(admin_client, entry, expected_status=expected_status)

    # Ensure that the entry didn't make it into the schedule
    entry_name = entry["name"]
    url = reverse_detail_url(entry_name)
    response = admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_validate_only_does_not_modify_schedule_with_bad_entry(admin_client):
    """A bad entry with validate_only should return 400 only."""
    # Ensure that a 400 "BAD REQUEST" is returned from the validator
    entry = TEST_SCHEDULE_ENTRY.copy()
    entry["interval"] = 1.5  # non-integer interval is invalid
    entry["validate_only"] = True
    expected_status = status.HTTP_400_BAD_REQUEST
    post_schedule(admin_client, entry, expected_status=expected_status)

    # Ensure that the entry didn't make it into the schedule
    url = reverse_detail_url(entry["name"])
    response = admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)
