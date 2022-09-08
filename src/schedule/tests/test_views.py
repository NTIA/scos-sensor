from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_SCHEDULE_ENTRY,
    post_schedule,
    reverse_detail_url,
)
from sensor import V1
from sensor.tests.utils import HTTPS_KWARG, validate_response
from test_utils.task_test_utils import simulate_frequency_fft_acquisitions


def test_entry_posted_to_schedule_is_immediately_available(admin_client):
    rjson = post_schedule(admin_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson["name"]
    entry_url = reverse_detail_url(entry_name)
    user_response = admin_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        assert rjson[k] == v

    validate_response(user_response, status.HTTP_200_OK)


def test_post_unknown_field_to_schedule(admin_client):
    """Unknown fields in a schedule entry should be ignored."""
    entry_json = TEST_SCHEDULE_ENTRY.copy()
    entry_json["nonsense"] = True
    rjson = post_schedule(admin_client, entry_json)
    entry_name = rjson["name"]
    entry_url = reverse_detail_url(entry_name)
    response = admin_client.get(entry_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        assert rjson[k] == v

    assert "nonsense" not in rjson
    assert "nonsense" not in response.data


def test_get_schedule(admin_client):
    url = reverse("schedule-list", kwargs=V1)
    rjson = validate_response(admin_client.get(url, **HTTPS_KWARG))
    assert rjson["results"] == EMPTY_SCHEDULE_RESPONSE

    post_schedule(admin_client, TEST_SCHEDULE_ENTRY)
    rjson = validate_response(admin_client.get(url, **HTTPS_KWARG))
    assert rjson["count"] == 1

    expected_name = TEST_SCHEDULE_ENTRY["name"]
    actual_name = rjson["results"][0]["name"]
    assert expected_name == actual_name


def test_get_nonexistent_entry_details_returns_404(admin_client):
    """Requesting details of non-existent entry should return 404."""
    url = reverse_detail_url("doesntexist")
    response = admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_get_existing_entry_details_returns_200(admin_client):
    """Requesting details of existing entry should return 200."""
    rjson = post_schedule(admin_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson["name"]
    url = reverse_detail_url(entry_name)
    response = admin_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_delete_entry_with_acquisitions_fails(admin_client, test_scheduler):
    """Attempting to delete entry with protected acquisitions should fail."""
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    entry_url = reverse_detail_url(entry_name)
    response = admin_client.delete(entry_url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_400_BAD_REQUEST)
    expected_status = status.HTTP_204_NO_CONTENT

    for acq_url in rjson["protected_objects"]:
        response = admin_client.delete(acq_url, **HTTPS_KWARG)
        validate_response(response, expected_status)

    response = admin_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, expected_status)
