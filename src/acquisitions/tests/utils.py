import json
from django.test import RequestFactory
from rest_framework.reverse import reverse
from rest_framework import status

from schedule.tests.utils import post_schedule
from scheduler.tests.utils import simulate_scheduler_run
from sensor import V1
from sensor.tests.utils import validate_response, HTTPS_KWARG


EMPTY_ACQUISITIONS_RESPONSE = []

SINGLE_ACQUISITION = {
    'name': 'test_acq',
    'start': None,
    'stop': None,
    'interval': None,
    'action': 'mock_acquire'
}

MULTIPLE_ACQUISITIONS = {
    'name': 'test_multiple_acq',
    'start': None,
    'relative_stop': 5,
    'interval': 1,
    'action': 'mock_acquire'
}


def simulate_acquisitions(client, n=1, is_private=False, name=None):
    assert 0 < n <= 10

    if n == 1:
        schedule_entry = SINGLE_ACQUISITION.copy()
    else:
        schedule_entry = MULTIPLE_ACQUISITIONS.copy()
        schedule_entry['relative_stop'] = n + 1

    schedule_entry['is_private'] = is_private

    if name is not None:
        schedule_entry['name'] = name

    entry = post_schedule(client, schedule_entry)
    simulate_scheduler_run(n)

    return entry['name']


def reverse_acquisitions_overview():
    rf = RequestFactory()
    request = rf.get('/acquisitions/', **HTTPS_KWARG)
    return reverse('acquisitions-overview', kwargs=V1, request=request)


def reverse_acquisition_list(schedule_entry_name):
    rf = RequestFactory()
    request = rf.get('/acquisitions/' + schedule_entry_name, **HTTPS_KWARG)
    kws = {'schedule_entry_name': schedule_entry_name}
    kws.update(V1)
    return reverse('acquisition-list', kwargs=kws, request=request)


def reverse_acquisition_detail(schedule_entry_name, task_id):
    rf = RequestFactory()
    url = '/acquisitions/' + schedule_entry_name + '/' + str(task_id)
    request = rf.get(url, **HTTPS_KWARG)
    kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}
    kws.update(V1)
    return reverse('acquisition-detail', kwargs=kws, request=request)


def reverse_acquisition_archive(schedule_entry_name, task_id):
    rf = RequestFactory()
    entry_name = schedule_entry_name
    url = '/'.join(['/acquisitions', entry_name, str(task_id), 'archive'])
    request = rf.get(url, **HTTPS_KWARG)
    kws = {'schedule_entry_name': entry_name, 'task_id': task_id}
    kws.update(V1)
    return reverse('acquisition-archive', kwargs=kws, request=request)


def get_acquisitions_overview(client):
    url = reverse_acquisitions_overview()
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def get_acquisition_list(client, schedule_entry_name):
    url = reverse_acquisition_list(schedule_entry_name)
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def get_acquisition_detail(client, schedule_entry_name, task_id):
    url = reverse_acquisition_detail(schedule_entry_name, task_id)
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def update_acquisition_detail(client, schedule_entry_name, task_id,
                              new_acquisition):
    url = reverse_acquisition_detail(schedule_entry_name, task_id)

    kwargs = {
        'data': json.dumps(new_acquisition),
        'content_type': 'application/json',
        'wsgi.url_scheme': 'https'
    }

    return client.put(url, **kwargs)
