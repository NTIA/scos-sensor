import datetime
import json

from django.test import RequestFactory
from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse

from schedule.models import ScheduleEntry
from schedule.tests.utils import TEST_SCHEDULE_ENTRY, post_schedule
from scheduler.tests.utils import simulate_scheduler_run
from sensor import V1
from sensor.tests.utils import HTTPS_KWARG, validate_response
from tasks.models import TaskResult

TEST_MAX_DISK_USAGE = 10
ONE_MICROSECOND = datetime.timedelta(0, 0, 1)

EMPTY_RESULTS_RESPONSE = []

EMPTY_ACQUISITIONS_RESPONSE = []

SINGLE_FREQUENCY_FFT_ACQUISITION = {
    "name": "test_acq",
    "start": None,
    "stop": None,
    "interval": None,
    "action": "test_single_frequency_m4s_action",
}

MULTIPLE_FREQUENCY_FFT_ACQUISITIONS = {
    "name": "test_multiple_acq",
    "start": None,
    "relative_stop": 5,
    "interval": 1,
    "action": "test_single_frequency_m4s_action",
}

SINGLE_TIMEDOMAIN_IQ_MULTI_RECORDING_ACQUISITION = {
    "name": "test_multirec_acq",
    "start": None,
    "stop": None,
    "interval": None,
    "action": "test_multi_frequency_iq_action",
}

SINGLE_TIMEDOMAIN_IQ_ACQUISITION = {
    "name": "test_time_domain_iq_acquire",
    "start": None,
    "stop": None,
    "interval": None,
    "action": "test_single_frequency_iq_action",
}


def simulate_acquisitions(client, schedule_entry, n=1, name=None):
    assert 0 < n <= 10

    if n > 1:
        schedule_entry["relative_stop"] = n

    if name is not None:
        schedule_entry["name"] = name

    entry = post_schedule(client, schedule_entry)
    simulate_scheduler_run(n)

    return entry["name"]


def simulate_frequency_fft_acquisitions(client, n=1, name=None):
    if n == 1:
        schedule_entry = SINGLE_FREQUENCY_FFT_ACQUISITION.copy()
    else:
        schedule_entry = MULTIPLE_FREQUENCY_FFT_ACQUISITIONS.copy()

    return simulate_acquisitions(client, schedule_entry, n, name)


def simulate_multirec_acquisition(client, name=None):
    schedule_entry = SINGLE_TIMEDOMAIN_IQ_MULTI_RECORDING_ACQUISITION.copy()
    return simulate_acquisitions(client, schedule_entry, n=1, name=name)


def simulate_timedomain_iq_acquisition(client, name=None):
    schedule_entry = SINGLE_TIMEDOMAIN_IQ_ACQUISITION.copy()
    return simulate_acquisitions(client, schedule_entry, n=1, name=name)


def create_task_results(n, admin_client, entry_name=None):
    # We need an entry in the schedule to create TRs for
    try:
        entry = ScheduleEntry.objects.get(name=entry_name)
    except Exception:
        test_entry = TEST_SCHEDULE_ENTRY
        if entry_name is not None:
            test_entry["name"] = entry_name

        rjson = post_schedule(admin_client, test_entry)
        entry_name = rjson["name"]
        entry = ScheduleEntry.objects.get(name=entry_name)

    for i in range(n):
        started = timezone.now()
        tr = TaskResult(
            schedule_entry=entry,
            task_id=i + 1,
            started=started,
            finished=started + ONE_MICROSECOND,
            duration=ONE_MICROSECOND,
            status="success",
            detail="",
        )
        tr.max_disk_usage = TEST_MAX_DISK_USAGE
        tr.save()

    return entry_name


def reverse_results_overview():
    rf = RequestFactory()
    request = rf.get("/tasks/completed/", **HTTPS_KWARG)
    return reverse("task-results-overview", kwargs=V1, request=request)


def reverse_result_list(schedule_entry_name):
    rf = RequestFactory()
    request = rf.get("/tasks/completed/" + schedule_entry_name, **HTTPS_KWARG)
    kws = {"schedule_entry_name": schedule_entry_name}
    kws.update(V1)
    return reverse("task-result-list", kwargs=kws, request=request)


def reverse_result_detail(schedule_entry_name, task_id):
    rf = RequestFactory()
    url = "/tasks/completed/" + schedule_entry_name + "/" + str(task_id)
    request = rf.get(url, **HTTPS_KWARG)
    kws = {"schedule_entry_name": schedule_entry_name, "task_id": task_id}
    kws.update(V1)
    return reverse("task-result-detail", kwargs=kws, request=request)


def reverse_archive(schedule_entry_name, task_id):
    rf = RequestFactory()
    entry_name = schedule_entry_name
    url = "/tasks/completed/{}/{!s}/archive".format(entry_name, task_id)
    request = rf.get(url, **HTTPS_KWARG)
    kws = {"schedule_entry_name": entry_name, "task_id": task_id}
    kws.update(V1)
    return reverse("task-result-archive", kwargs=kws, request=request)


def reverse_archive_all(schedule_entry_name):
    rf = RequestFactory()
    entry_name = schedule_entry_name
    url = "/tasks/completed/{}/archive".format(entry_name)
    request = rf.get(url, **HTTPS_KWARG)
    kws = {"schedule_entry_name": entry_name}
    kws.update(V1)
    return reverse("task-result-list-archive", kwargs=kws, request=request)


def get_results_overview(client):
    url = reverse_results_overview()
    response = client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_200_OK)
    return rjson["results"]


def get_result_list(client, schedule_entry_name):
    url = reverse_result_list(schedule_entry_name)
    response = client.get(url, **HTTPS_KWARG)
    rjson = validate_response(response, status.HTTP_200_OK)
    return rjson["results"]


def get_result_detail(client, schedule_entry_name, task_id):
    url = reverse_result_detail(schedule_entry_name, task_id)
    response = client.get(url, **HTTPS_KWARG)
    return validate_response(response, status.HTTP_200_OK)


def update_result_detail(client, schedule_entry_name, task_id, new_acquisition):
    url = reverse_result_detail(schedule_entry_name, task_id)

    kwargs = {
        "data": json.dumps(new_acquisition),
        "content_type": "application/json",
        "wsgi.url_scheme": "https",
    }

    return client.put(url, **kwargs)
