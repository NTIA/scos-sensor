import pytest

from tasks.models import TaskResult
from tasks.tests.utils import TEST_MAX_TASK_RESULTS, create_task_results


@pytest.mark.django_db
def test_max_results(user_client):
    """TaskResults are not managed by user, so oldest should be deleted."""
    create_task_results(TEST_MAX_TASK_RESULTS + 10, user_client)
    assert TaskResult.objects.count() == TEST_MAX_TASK_RESULTS


@pytest.mark.django_db
def test_str(user_client):
    create_task_results(1, user_client)
    str(TaskResult.objects.get())
