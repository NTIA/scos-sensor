import datetime

import pytest
from django.utils import timezone

from results.models import TaskResult
from schedule.models import ScheduleEntry
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule


TEST_MAX_TASK_RESULTS = 100  # Reduce from default of settings.MAX_TASK_RESULTS
ONE_MICROSECOND = datetime.timedelta(0, 0, 1)


def create_task_results(n, user_client):
    # We need an entry in the schedule to create TRs for
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    entry = ScheduleEntry.objects.get(name=entry_name)

    for i in range(n):
        started = timezone.now()
        tr = TaskResult(
            schedule_entry=entry,
            task_id=i+1,
            started=started,
            finished=started+ONE_MICROSECOND,
            duration=ONE_MICROSECOND,
            result='result',
            detail=''
        )
        tr.max_results = TEST_MAX_TASK_RESULTS
        tr.save()


@pytest.mark.django_db
def test_max_results(user_client):
    """TaskResults are not managed by user, so oldest should be deleted."""
    create_task_results(TEST_MAX_TASK_RESULTS + 10, user_client)
    assert TaskResult.objects.count() == TEST_MAX_TASK_RESULTS


@pytest.mark.django_db
def test_str(user_client):
    create_task_results(1, user_client)
    str(TaskResult.objects.get())
