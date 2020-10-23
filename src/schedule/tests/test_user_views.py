import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    post_schedule,
)
from sensor import V1
from sensor.tests.utils import HTTPS_KWARG, validate_response


def test_user_cannot_view_schedule_entry_list(user_client):
    url = reverse("schedule-list", kwargs=V1)
    response = user_client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_403_FORBIDDEN)
    assert rjson != EMPTY_SCHEDULE_RESPONSE

def test_user_cannot_post_schedule(user_client):
    post_schedule(user_client, TEST_PRIVATE_SCHEDULE_ENTRY, expected_status=status.HTTP_403_FORBIDDEN)

def test_user_cannot_view_schedule_entry_detail(user_client, admin_client):
    admin_rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    admin_entry_name = admin_rjson["name"]
    kws = {"pk": admin_entry_name}
    kws.update(V1)
    admin_url = reverse("schedule-detail", kwargs=kws)
    response = user_client.get(admin_url)
    rjson = validate_response(response, status.HTTP_403_FORBIDDEN)
    assert rjson != EMPTY_SCHEDULE_RESPONSE



