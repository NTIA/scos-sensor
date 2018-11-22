from rest_framework.reverse import reverse

from sensor import V1
from .utils import validate_response, HTTPS_KWARG

API_ROOT_ENDPOINTS = {
    'acquisitions', 'users', 'schedule', 'status', 'capabilities', 'results'
}


def test_index(user_client):
    response = user_client.get(reverse('api-root', kwargs=V1), **HTTPS_KWARG)
    rjson = validate_response(response)

    assert rjson.keys() == API_ROOT_ENDPOINTS
