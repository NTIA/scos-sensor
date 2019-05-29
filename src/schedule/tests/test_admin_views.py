from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_SCHEDULE_ENTRY,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    post_schedule,
    update_schedule,
)
from sensor import V1
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_post_admin_private_schedule(admin_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson["name"]
    kws = {"pk": entry_name}
    kws.update(V1)
    entry_url = reverse("schedule-detail", kwargs=kws)
    admin_user_respose = admin_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_PRIVATE_SCHEDULE_ENTRY.items():
        assert rjson[k] == v

    assert rjson["is_private"]
    validate_response(admin_user_respose, status.HTTP_200_OK)
    assert admin_user_respose.data["is_private"]


def test_admin_can_view_private_entry_in_list(admin_client):
    post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    url = reverse("schedule-list", kwargs=V1)
    response = admin_client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_200_OK)
    assert rjson != EMPTY_SCHEDULE_RESPONSE


def test_admin_can_view_all_entries(admin_client, user_client, alt_admin_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson["name"]
    kws = {"pk": user_entry_name}
    kws.update(V1)
    user_url = reverse("schedule-detail", kwargs=kws)

    # alt admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]
    kws = {"pk": alt_admin_entry_name}
    kws.update(V1)
    alt_admin_url = reverse("schedule-detail", kwargs=kws)

    response = admin_client.get(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)

    response = admin_client.get(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_admin_can_delete_all_entries(admin_client, user_client, alt_admin_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson["name"]
    kws = {"pk": user_entry_name}
    kws.update(V1)
    user_url = reverse("schedule-detail", kwargs=kws)

    # admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]
    kws = {"pk": alt_admin_entry_name}
    kws.update(V1)
    alt_admin_url = reverse("schedule-detail", kwargs=kws)

    response = admin_client.delete(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    response = admin_client.delete(user_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)

    response = admin_client.delete(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)
    response = admin_client.delete(alt_admin_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_admin_can_modify_all_entries(admin_client, user_client, alt_admin_client):
    # user schedule entry
    user_rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    user_entry_name = user_rjson["name"]

    admin_adjust_user_response = update_schedule(
        admin_client, user_entry_name, TEST_PRIVATE_SCHEDULE_ENTRY
    )

    # admin user schedule entry
    alt_admin_rjson = post_schedule(alt_admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    alt_admin_entry_name = alt_admin_rjson["name"]

    admin_adjust_alt_admin_response = update_schedule(
        admin_client, alt_admin_entry_name, TEST_SCHEDULE_ENTRY
    )

    validate_response(admin_adjust_user_response, status.HTTP_200_OK)
    assert admin_adjust_user_response.data["is_private"]
    validate_response(admin_adjust_alt_admin_response, status.HTTP_200_OK)
    assert not admin_adjust_alt_admin_response.data["is_private"]


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
    assert admin_user_respose.data["is_private"]
