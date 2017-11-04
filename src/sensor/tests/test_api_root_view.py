from rest_framework.reverse import reverse

from .utils import validate_response, HTTPS_KWARG


API_ROOT_ENDPOINTS = {
    'acquisitions',
    'users',
    'schedule',
    'status',
    'capabilities'
}


def test_index(user_client):
    response = user_client.get(reverse('v1:api-root'), **HTTPS_KWARG)
    rjson = validate_response(response)

    assert set(rjson.keys()) == API_ROOT_ENDPOINTS  # py2.7 compat, set(keys)
