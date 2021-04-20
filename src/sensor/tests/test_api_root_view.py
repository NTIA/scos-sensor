from rest_framework.reverse import reverse

from sensor import V1

from .utils import HTTPS_KWARG, validate_response

API_ROOT_ENDPOINTS = {"users", "schedule", "status", "capabilities", "tasks"}


def test_index(admin_client):
    response = admin_client.get(reverse("api-root", kwargs=V1), **HTTPS_KWARG)
    rjson = validate_response(response)

    assert rjson.keys() == API_ROOT_ENDPOINTS
