from rest_framework import status
from rest_framework.reverse import reverse

from acquisitions.tests.utils import simulate_acquisitions
from schedule.tests.utils import (
    EMPTY_SCHEDULE_RESPONSE,
    TEST_SCHEDULE_ENTRY,
    TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_NONSENSE_SCHEDULE_ENTRY,
    post_schedule,
    reverse_detail_url
)
from sensor import V1
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_post_schedule(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        assert rjson[k] == v

    validate_response(user_respose, status.HTTP_200_OK)


def test_post_nonsense_schedule(user_client):
    rjson = post_schedule(user_client, TEST_NONSENSE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        assert rjson[k] == v

    assert 'nonsense' not in rjson
    validate_response(user_respose, status.HTTP_200_OK)
    assert 'nonsense' not in user_respose.data


def test_private_schedule_is_private(admin_client, user_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse_detail_url(entry_name)
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)
    admin_user_respose = admin_client.get(entry_url, **HTTPS_KWARG)

    validate_response(user_respose, status.HTTP_403_FORBIDDEN)
    validate_response(admin_user_respose, status.HTTP_200_OK)


def test_get_schedule(user_client):
    url = reverse('schedule-list', kwargs=V1)
    rjson = validate_response(user_client.get(url, **HTTPS_KWARG))
    assert rjson == EMPTY_SCHEDULE_RESPONSE

    post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    rjson = validate_response(user_client.get(url, **HTTPS_KWARG))
    assert len(rjson) == 1

    expected_name = TEST_SCHEDULE_ENTRY['name']
    actual_name = rjson[0]['name']
    assert expected_name == actual_name


def test_get_nonexistent_entry_details_returns_404(user_client):
    """Requesting details of non-existent entry should return 404."""
    url = reverse_detail_url('doesntexist')
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_get_existing_entry_details_returns_200(user_client):
    """Requesting details of existing entry should return 200."""
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse_detail_url(entry_name)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, **HTTPS_KWARG)


def test_delete_entry_with_acquisitions_fails(user_client, test_scheduler):
    """Attempting to delete entry with protected acquisitions should fail."""
    entry_name = simulate_acquisitions(user_client)
    entry_url = reverse_detail_url(entry_name)
    response = user_client.delete(entry_url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_400_BAD_REQUEST)
    expected_status = status.HTTP_204_NO_CONTENT

    for acq_url in rjson['protected_objects']:
        response = user_client.delete(acq_url, **HTTPS_KWARG)
        validate_response(response, expected_status)

    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, expected_status)
