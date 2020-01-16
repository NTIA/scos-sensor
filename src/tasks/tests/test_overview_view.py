from rest_framework import status

from sensor.tests.utils import HTTPS_KWARG, validate_response
from tasks.tests.utils import (
    EMPTY_RESULTS_RESPONSE,
    create_task_results,
    get_results_overview,
    reverse_results_overview,
    simulate_frequency_fft_acquisitions,
)


def test_user_empty_overview_response(user_client):
    response = get_results_overview(user_client)
    assert response == EMPTY_RESULTS_RESPONSE


def test_admin_empty_overview_response(admin_client):
    response = get_results_overview(admin_client)
    assert response == EMPTY_RESULTS_RESPONSE


def test_user_get_overview(user_client):
    create_task_results(2, user_client)
    overview, = get_results_overview(user_client)
    assert overview["task_results_available"] == 2
    assert overview["archive"] is None  # indicates no acquisition data available
    assert overview["task_results"]  # is non-empty string
    assert overview["schedule_entry"]  # is non-empty string


def test_admin_get_overview(admin_client):
    create_task_results(2, admin_client)
    overview, = get_results_overview(admin_client)
    assert overview["task_results_available"] == 2
    assert overview["archive"] is None  # indicates no acquisition data available
    assert overview["task_results"]  # is non-empty string
    assert overview["schedule_entry"]  # is non-empty string


def test_overview_for_private_entry_is_private(
    admin_client, user_client, test_scheduler
):
    simulate_frequency_fft_acquisitions(admin_client, is_private=True)
    overview = get_results_overview(user_client)
    assert overview == []

    overview, = get_results_overview(admin_client)
    assert overview["task_results_available"] == 1
    assert overview["task_results"]  # is non-empty string
    assert overview["schedule_entry"]  # is non-empty string


def test_user_delete_overview_not_allowed(user_client):
    url = reverse_results_overview()
    response = user_client.delete(url, **HTTPS_KWARG)
    assert validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)


def test_admin_delete_overview_not_allowed(admin_client):
    url = reverse_results_overview()
    response = admin_client.delete(url, **HTTPS_KWARG)
    assert validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)
