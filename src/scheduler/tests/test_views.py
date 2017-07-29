import json

import pytest

from rest_framework import status
from rest_framework.reverse import reverse


EMPTY_SCHEDULE_REPONSE = []

TEST_SCHEDULE_ENTRY = {'name': 'test', 'action': 'logger'}

API_ROOT_ENDPOINTS = {
    'schedule',
    'scheduler',
    'acquisitions',
    #'capabilities'
}


def post_schedule(client, entry):
    r = client.post(reverse('v1:schedule-list'),
                    data=json.dumps(entry),
                    content_type='application/json')
    rjson = r.json()
    assert r.status_code == status.HTTP_201_CREATED, rjson
    return rjson


def validate_response(response, expected_code=None):
    actual_code = response.status_code
    if expected_code is None:
        assert status.is_success(actual_code)
    else:
        assert actual_code == expected_code, response.context

    if actual_code not in (status.HTTP_204_NO_CONTENT,):
        rjson = response.json()
        return rjson


def test_index(client):
    rjson = validate_response(client.get(reverse('v1:api-root')))
    assert rjson.keys() == API_ROOT_ENDPOINTS


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
