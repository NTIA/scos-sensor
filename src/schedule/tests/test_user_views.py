from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests import (
    EMPTY_SCHEDULE_REPONSE, TEST_SCHEDULE_ENTRY, TEST_PRIVATE_SCHEDULE_ENTRY,
    TEST_NONSENSE_SCHEDULE_ENTRY)
from schedule.tests.utils import post_schedule, update_schedule
from sensor.tests.utils import validate_response


HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def test_post_user_private_schedule(user_client):
    rjson = post_schedule(user_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry_url = reverse('v1:schedule-detail', [entry_name])
    user_respose = user_client.get(entry_url, **HTTPS_KWARG)

    assert not rjson['is_private']
    validate_response(user_respose, status.HTTP_200_OK)
    assert not user_respose.data['is_private']


def test_user_cant_delete_admin_entry(admin_client, user_client):
    rjson = post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    url = reverse('v1:schedule-detail', [entry_name])

    response = user_client.delete(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_403_FORBIDDEN)
