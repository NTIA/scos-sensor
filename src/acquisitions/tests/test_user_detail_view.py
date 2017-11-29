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
                                                     alternate_user_client,
                                                     testclock):
    # alternate user schedule entry
    alternate_user_entry_name = simulate_acquisitions(
        alternate_user_client, name='alternate_user_single_acq')
    alternate_user_acq_url = reverse_acquisition_detail(
        alternate_user_entry_name, 1)

    user_view_alternate_user_response = user_client.get(
        alternate_user_acq_url, **HTTPS_KWARG)

    # admin user schedule entry
    admin_entry_name = simulate_acquisitions(
        admin_client, name='admin_single_acq')
    admin_entry_url = reverse_acquisition_detail(admin_entry_name, 1)

    user_view_admin_response = user_client.get(admin_entry_url, **HTTPS_KWARG)

    validate_response(user_view_alternate_user_response, status.HTTP_200_OK)
    validate_response(user_view_admin_response, status.HTTP_200_OK)
