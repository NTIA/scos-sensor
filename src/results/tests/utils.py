import datetime

from django.test import RequestFactory
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework import status

from results.models import TaskResult
from schedule.models import ScheduleEntry
from schedule.tests.utils import post_schedule, TEST_SCHEDULE_ENTRY
from sensor import V1
from sensor.tests.utils import validate_response, HTTPS_KWARG

TEST_MAX_TASK_RESULTS = 100  # Reduce from default of settings.MAX_TASK_RESULTS
ONE_MICROSECOND = datetime.timedelta(0, 0, 1)

EMPTY_RESULTS_RESPONSE = []


def create_task_results(n, user_client, entry_name=None):
    # We need an entry in the schedule to create TRs for
    try:
        entry = ScheduleEntry.objects.get(name=entry_name)
    except Exception:
        test_entry = TEST_SCHEDULE_ENTRY
        if entry_name is not None:
            test_entry['name'] = entry_name

        rjson = post_schedule(user_client, test_entry)
        entry_name = rjson['name']
        entry = ScheduleEntry.objects.get(name=entry_name)

    for i in range(n):
        started = timezone.now()
        tr = TaskResult(
            schedule_entry=entry,
            task_id=i + 1,
            started=started,
            finished=started + ONE_MICROSECOND,
            duration=ONE_MICROSECOND,
            result='success',
            detail='')
        tr.max_results = TEST_MAX_TASK_RESULTS
        tr.save()

    return entry_name


def reverse_results_overview():
    rf = RequestFactory()
    request = rf.get('/results/', **HTTPS_KWARG)
    return reverse('results-overview', kwargs=V1, request=request)


def reverse_result_list(schedule_entry_name):
    rf = RequestFactory()
    request = rf.get('/results/' + schedule_entry_name, **HTTPS_KWARG)
    kws = {'schedule_entry_name': schedule_entry_name}
    kws.update(V1)
    return reverse('result-list', kwargs=kws, request=request)


def reverse_result_detail(schedule_entry_name, task_id):
    rf = RequestFactory()
    url = '/results/' + schedule_entry_name + '/' + str(task_id)
    request = rf.get(url, **HTTPS_KWARG)
    kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}
    kws.update(V1)
    return reverse('result-detail', kwargs=kws, request=request)


def get_results_overview(client):
    url = reverse_results_overview()
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def get_result_list(client, schedule_entry_name):
    url = reverse_result_list(schedule_entry_name)
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def get_result_detail(client, schedule_entry_name, task_id):
    url = reverse_result_detail(schedule_entry_name, task_id)
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)
