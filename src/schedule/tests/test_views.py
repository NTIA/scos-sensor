from rest_framework import status
from rest_framework.reverse import reverse

from acquisitions.tests.utils import simulate_acquisitions
from schedule.tests import (
    EMPTY_SCHEDULE_REPONSE, TEST_SCHEDULE_ENTRY, TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_NONSENSE_SCHEDULE_ENTRY)
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response


HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def test_post_schedule(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse('v1:schedule-detail', [entry_name])
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        rjson[k] == v

    validate_response(user_respose, status.HTTP_200_OK)


def test_post_nonsense_schedule(user_client):
    rjson = post_schedule(user_client, TEST_NONSENSE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse('v1:schedule-detail', [entry_name])
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        rjson[k] == v

    assert 'nonsense' not in rjson
    validate_response(user_respose, status.HTTP_200_OK)
    assert 'nonsense' not in user_respose.data


def test_private_schedule_is_private(admin_client, user_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse('v1:schedule-detail', [entry_name])

    user_respose = user_client.get(entry_url, **HTTPS_KWARG)
    admin_user_respose = admin_client.get(entry_url, **HTTPS_KWARG)

    validate_response(user_respose, status.HTTP_403_FORBIDDEN)
    validate_response(admin_user_respose, status.HTTP_200_OK)


def test_get_schedule(user_client):
    url = reverse('v1:schedule-list')
    rjson = validate_response(user_client.get(url, **HTTPS_KWARG))
    assert rjson == EMPTY_SCHEDULE_REPONSE

    post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    rjson = validate_response(user_client.get(url, **HTTPS_KWARG))
    assert len(rjson) == 1

    expected_name = TEST_SCHEDULE_ENTRY['name']
    actual_name = rjson[0]['name']
    assert expected_name == actual_name


def test_get_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    bad_url = reverse('v1:schedule-detail', ['doesntexist'])
    good_url = reverse('v1:schedule-detail', [entry_name])

    response = user_client.get(bad_url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)

    validate_response(user_client.get(good_url, **HTTPS_KWARG))


def test_delete_entry(user_client):
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse('v1:schedule-detail', [entry_name])

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_204_NO_CONTENT)

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_delete_entry_with_acquisitions_fails(user_client, testclock):
    entry_name = simulate_acquisitions(user_client, n=1)
    entry_url = reverse('v1:schedule-detail', [entry_name])
    response = user_client.delete(entry_url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_400_BAD_REQUEST)
    expected_status = status.HTTP_204_NO_CONTENT

    for acq_url in rjson['protected_objects']:
        response = user_client.delete(acq_url, **HTTPS_KWARG)
        validate_response(response, expected_status)

    response = user_client.delete(entry_url, **HTTPS_KWARG)
    validate_response(response, expected_status)
