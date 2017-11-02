from django.test import RequestFactory
from rest_framework.reverse import reverse
from rest_framework import status

from acquisitions.tests import SINGLE_ACQUISITION, MULTIPLE_ACQUISITIONS
from schedule.tests.utils import post_schedule
from scheduler.tests.utils import simulate_scheduler_run
from sensor.tests.utils import validate_response

HTTPS_KWARG = {'wsgi.url_scheme': 'https'}


def simulate_acquisitions(client, n=1):
    assert 0 < n <= 10

    if n == 1:
        schedule_entry = SINGLE_ACQUISITION
    else:
        schedule_entry = MULTIPLE_ACQUISITIONS
        schedule_entry['stop'] = n + 1

    entry = post_schedule(client, schedule_entry)
    simulate_scheduler_run(n)

    return entry['name']


def reverse_acquisitions_overview():
    rf = RequestFactory()

    request = rf.get('/api/v1/acquisitions', **HTTPS_KWARG)

    return reverse('v1:acquisitions-overview', request=request)


def reverse_acquisition_list(schedule_entry_name):
    rf = RequestFactory()

    request = rf.get('/acquisitions/' + schedule_entry_name, **HTTPS_KWARG)
    kws = {'schedule_entry_name': schedule_entry_name}

    return reverse('v1:acquisition-list', kwargs=kws, request=request)


def reverse_acquisition_detail(schedule_entry_name, task_id):
    rf = RequestFactory()
    task_str = str(task_id)
    request = rf.get('/acquisitions/' + schedule_entry_name + '/' + task_str)
    kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}

    return reverse('v1:acquisition-detail', kwargs=kws, request=request)


def reverse_acquisition_archive(schedule_entry_name, task_id):
    rf = RequestFactory()
    entry_name = schedule_entry_name
    task_str = str(task_id)
    url_str = '/'.join(['/acquisitions', entry_name, task_str, 'archive'])
    request = rf.get(url_str)
    kws = {'schedule_entry_name': entry_name, 'task_id': task_id}

    return reverse('v1:acquisition-archive', kwargs=kws, request=request)


def get_acquisitions_overview(client):
    url = reverse_acquisitions_overview()
    response = client.get(url, **HTTPS_KWARG)

    return validate_response(response, status.HTTP_200_OK)


def get_acquisition_list(client, schedule_entry_name):
    url = reverse_acquisition_list(schedule_entry_name)
    response = client.get(url)

    return validate_response(response, status.HTTP_200_OK)


def get_acquisition_detail(client, schedule_entry_name, task_id):
    url = reverse_acquisition_detail(schedule_entry_name, task_id)
    response = client.get(url)

    return validate_response(response, status.HTTP_200_OK)
