from rest_framework import status
from rest_framework.reverse import reverse

from schedule.tests.utils import TEST_PRIVATE_SCHEDULE_ENTRY, post_schedule
from sensor import V1
from sensor.tests.utils import HTTPS_KWARG, validate_response


def test_user_cannot_view_user_list(admin_client, user_client):
    """An unprivileged user should not be able to see private entries."""
    post_schedule(admin_client, TEST_PRIVATE_SCHEDULE_ENTRY)
    url = reverse("user-list", kwargs=V1)
    response = user_client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_403_FORBIDDEN)
    assert "results" not in rjson
