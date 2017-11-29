from rest_framework import status
from rest_framework.reverse import reverse

from acquisitions.tests.utils import (
    reverse_acquisition_detail,
    get_acquisition_detail,
    simulate_acquisitions,
    HTTPS_KWARG
)
from sensor.tests.utils import validate_response


def test_user_can_view_other_nonprivate_acquisitions(admin_client, user_client,
                                                     alternate_admin_client,
                                                     testclock):
    # admin user schedule entry
    admin_entry_name = simulate_acquisitions(admin_client)
    admin_acq_url = reverse_acquisition_detail(admin_entry_name, 1)

    user_view_admin_response = user_client.get(admin_acq_url, **HTTPS_KWARG)
    alternate_admin_client_view_admin_responce = alternate_admin_client.get(
        admin_acq_url, **HTTPS_KWARG)

    validate_response(user_view_admin_response, status.HTTP_200_OK)
    validate_response(
        alternate_admin_client_view_admin_responce, status.HTTP_200_OK)
