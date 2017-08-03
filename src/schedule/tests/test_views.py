import pytest

from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests import EMPTY_SCHEDULE_REPONSE, TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response


@pytest.mark.django_db
def test_post_schedule(client):
    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)
    for k, v in TEST_SCHEDULE_ENTRY.items():
        rjson[k] == v


@pytest.mark.django_db
def test_get_schedule(client):
    url = reverse('v1:schedule-list')
    rjson = validate_response(client.get(url))
    assert rjson == EMPTY_SCHEDULE_REPONSE
    post_schedule(client, TEST_SCHEDULE_ENTRY)
    rjson = validate_response(client.get(url))
    assert len(rjson) == 1
    expected_name = TEST_SCHEDULE_ENTRY['name']
    actual_name = rjson[0]['name']
    assert expected_name == actual_name


@pytest.mark.django_db
def test_get_entry(client):
    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    bad_url = reverse('v1:schedule-detail', kwargs={'name': 'doesntexist'})
    good_url = reverse('v1:schedule-detail', kwargs={'name': entry_name})
    validate_response(client.get(bad_url), status.HTTP_404_NOT_FOUND)
    validate_response(client.get(good_url))


@pytest.mark.django_db
def test_delete_entry(client):
    rjson = post_schedule(client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse('v1:schedule-detail', kwargs={'name': entry_name})
    validate_response(client.delete(url), status.HTTP_204_NO_CONTENT)
    validate_response(client.delete(url), status.HTTP_404_NOT_FOUND)
