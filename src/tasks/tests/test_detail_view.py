from rest_framework import status

from sensor.tests.utils import validate_response, HTTPS_KWARG
from tasks.tests.utils import (
    create_task_results, reverse_result_detail, simulate_acquisitions)


def test_can_view_own_result_details(user_client):
    """A user should be able to view results they create."""
    entry_name = create_task_results(1, user_client)
    url = reverse_result_detail(entry_name, 1)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_can_view_others_result_details(user_client, alt_user_client):
    """A user should be able to view results created by others."""
    entry_name = create_task_results(1, user_client)
    url = reverse_result_detail(entry_name, 1)
    response = alt_user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_200_OK)


def test_cannot_view_private_result_details(user_client, admin_client,
                                            test_scheduler):
    """A user should not be able to view the result of a private task."""
    entry_name = simulate_acquisitions(admin_client, is_private=True)
    url = reverse_result_detail(entry_name, 1)
    response = user_client.get(url, **HTTPS_KWARG)
    validate_response(response, status.HTTP_404_NOT_FOUND)


def test_cannot_delete_result_details(user_client):
    """Results are read-only."""
    entry_name = create_task_results(1, user_client)
    url = reverse_result_detail(entry_name, 1)
    response = user_client.delete(url, **HTTPS_KWARG)

    validate_response(response, status.HTTP_405_METHOD_NOT_ALLOWED)
