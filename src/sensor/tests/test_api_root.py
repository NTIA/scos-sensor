from rest_framework.reverse import reverse

from .utils import validate_response


API_ROOT_ENDPOINTS = {
    'acquisitions',
    'schedule',
    'status',
    # 'capabilities'
}


def test_index(client):
    rjson = validate_response(client.get(reverse('v1:api-root')))
    assert set(rjson.keys()) == API_ROOT_ENDPOINTS  # py2.7 compat, set(keys)
