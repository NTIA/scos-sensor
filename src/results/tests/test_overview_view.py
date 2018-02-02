from rest_framework import status

from acquisitions.tests.utils import simulate_acquisitions
from results.tests.utils import (
    EMPTY_RESULTS_RESPONSE,
    create_task_results,
    reverse_results_overview,
    get_results_overview
)
from sensor.tests.utils import validate_response, HTTPS_KWARG


def test_empty_overview_response(user_client):
    response = get_results_overview(user_client)
    assert response == EMPTY_RESULTS_RESPONSE


def test_get_overview(user_client):
    create_task_results(2, user_client)
    overview, = get_results_overview(user_client)
    assert overview['results_available'] == 2
    assert overview['url']  # is non-empty string
    assert overview['schedule_entry']  # is non-empty string


def test_overview_for_private_entry_is_private(admin_client, user_client,
                                               test_scheduler):
    simulate_acquisitions(admin_client, is_private=True)
    overview = get_results_overview(user_client)
    assert overview == []

    overview, = get_results_overview(admin_client)
    assert overview['results_available'] == 1
    assert overview['url']  # is non-empty string
    assert overview['schedule_entry']  # is non-empty string


def test_delete_overview_not_allowed(user_client):
    url = reverse_results_overview()
    response = user_client.delete(url, **HTTPS_KWARG)
    assert validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)
