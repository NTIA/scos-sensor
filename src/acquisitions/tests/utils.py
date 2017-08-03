from django.test import RequestFactory
from rest_framework.reverse import reverse

from acquisitions.tests import SINGLE_ACQUISITION, MULTIPLE_ACQUISITIONS
from schedule.tests.utils import post_schedule
from scheduler.tests.utils import simulate_scheduler_run
from sensor.tests.utils import validate_response


def simulate_acquisitions(client, n=1):
    assert 1 < n <= 10

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
    request = rf.get('/api/v1/acquisitions')
    return reverse('v1:acquisitions-overview', request=request)


def reverse_acquisitions_preview(schedule_entry_name):
    rf = RequestFactory()
    request = rf.get('/acquisitions/' + schedule_entry_name)
    kws = {'schedule_entry_name': schedule_entry_name}
    return reverse('v1:acquisitions-preview', kwargs=kws, request=request)


def get_acquisitions_overview(client):
    url = reverse_acquisitions_overview()
    response = client.get(url)
    return validate_response(response, 200)


def get_acquisitions_preview(client, schedule_entry_name):
    url = reverse_acquisitions_preview(schedule_entry_name)
    response = client.get(url)
    return validate_response(response, 200)
