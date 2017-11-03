import pytest
from rest_framework.reverse import reverse

from .utils import validate_response, HTTPS_KWARG


API_ROOT_ENDPOINTS = {
    'acquisitions',
    'users',
    'schedule',
    'status',
    'capabilities'
}


@pytest.mark.django_db
def test_index(client, test_user):
    client.login(username=test_user.username, password=test_user.password)

    rjson = validate_response(
        client.get(reverse('v1:api-root'), **HTTPS_KWARG))

    assert set(rjson.keys()) == API_ROOT_ENDPOINTS  # py2.7 compat, set(keys)
