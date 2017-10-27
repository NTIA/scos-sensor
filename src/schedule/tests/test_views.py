import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from acquisitions.tests.utils import simulate_acquisitions
from schedule.tests import EMPTY_SCHEDULE_REPONSE, TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response

HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


@pytest.mark.django_db
def test_post_schedule(client, test_user):
    client.login(username=test_user[0], password=test_user[1])

    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)

    for k, v in TEST_SCHEDULE_ENTRY.items():
        rjson[k] == v


@pytest.mark.django_db
def test_get_schedule(client, test_user):
    client.login(username=test_user[0], password=test_user[1])

    url = reverse('v1:schedule-list')

    rjson = validate_response(client.get(url, **HTTPS_KWARG))

    assert rjson == EMPTY_SCHEDULE_REPONSE

    post_schedule(client, TEST_SCHEDULE_ENTRY)
    rjson = validate_response(client.get(url, **HTTPS_KWARG))

    assert len(rjson) == 1

    expected_name = TEST_SCHEDULE_ENTRY['name']
    actual_name = rjson[0]['name']

    assert expected_name == actual_name


@pytest.mark.django_db
def test_get_entry(client, test_user):
    client.login(username=test_user[0], password=test_user[1])

    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)

    entry_name = rjson['name']

    bad_url = reverse('v1:schedule-detail', ['doesntexist'])
    good_url = reverse('v1:schedule-detail', [entry_name])

    validate_response(
        client.get(bad_url, **HTTPS_KWARG), status.HTTP_404_NOT_FOUND)

    validate_response(client.get(good_url, **HTTPS_KWARG))


@pytest.mark.django_db
def test_delete_entry(client, test_user):
    client.login(username=test_user[0], password=test_user[1])

    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)

    entry_name = rjson['name']

    url = reverse('v1:schedule-detail', [entry_name])

    validate_response(
        client.delete(url, **HTTPS_KWARG), status.HTTP_204_NO_CONTENT)

    validate_response(
        client.delete(url, **HTTPS_KWARG), status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
def test_delete_entry_with_acquisitions_fails(client, testclock, test_user):
    client.login(username=test_user[0], password=test_user[1])

    entry_name = simulate_acquisitions(client, n=1)

    entry_url = reverse('v1:schedule-detail', [entry_name])

    rjson = validate_response(client.delete(entry_url, **HTTPS_KWARG),
                              status.HTTP_400_BAD_REQUEST)

    for acq_url in rjson['protected_objects']:
        validate_response(
            client.delete(acq_url, **HTTPS_KWARG), status.HTTP_204_NO_CONTENT)

    validate_response(
        client.delete(entry_url, **HTTPS_KWARG), status.HTTP_204_NO_CONTENT)
