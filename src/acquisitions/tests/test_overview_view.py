from rest_framework import status

from acquisitions.tests.utils import (
    SINGLE_ACQUISITION,
    EMPTY_ACQUISITIONS_RESPONSE,
    reverse_acquisitions_overview,
    reverse_acquisition_list,
    simulate_acquisitions,
    get_acquisitions_overview
)
from schedule.tests.utils import post_schedule
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_empty_overview_response(user_client):
    response = get_acquisitions_overview(user_client)
    assert response == EMPTY_ACQUISITIONS_RESPONSE


def test_overview_exists_when_entry_created(user_client, test_scheduler):
    post_schedule(user_client, SINGLE_ACQUISITION)
    overview, = get_acquisitions_overview(user_client)
    assert overview['acquisitions_available'] == 0


def test_get_overview(user_client, test_scheduler):
    entry1_name = simulate_acquisitions(user_client)
    overview, = get_acquisitions_overview(user_client)

    assert overview['url'] == reverse_acquisition_list(entry1_name)
    assert overview['acquisitions_available'] == 1

    entry2_name = simulate_acquisitions(user_client, n=3)
    overview_list = get_acquisitions_overview(user_client)

    assert len(overview_list) == 2

    (overview1, overview2) = overview_list

    assert overview1 == overview
    assert overview2['url'] == reverse_acquisition_list(entry2_name)
    assert overview2['acquisitions_available'] == 3


def test_overview_for_private_entry_is_private(admin_client, user_client,
                                               test_scheduler):
    simulate_acquisitions(admin_client, is_private=True)
    overview = get_acquisitions_overview(user_client)
    assert overview == []

    overview, = get_acquisitions_overview(admin_client)
    assert overview['acquisitions_available'] == 1
    assert overview['url']  # is non-empty string
    assert overview['schedule_entry']  # is non-empty string


def test_delete_overview_not_allowed(user_client, test_scheduler):
    url = reverse_acquisitions_overview()
    response = user_client.delete(url, **HTTPS_KWARG)
    assert validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)
