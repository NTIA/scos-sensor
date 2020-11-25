import json
import os
from os import path

from django.conf import settings

from actions.tests.utils import check_metadata_fields
from sigmf.validate import validate as sigmf_validate
from tasks.models import Acquisition, TaskResult
from tasks.tests.utils import (
    MULTIPLE_FREQUENCY_FFT_ACQUISITIONS,
    SINGLE_FREQUENCY_FFT_ACQUISITION,
    simulate_frequency_fft_acquisitions,
)

SCHEMA_DIR = path.join(settings.REPO_ROOT, "schemas")
SCHEMA_FNAME = "scos_transfer_spec_schema.json"
SCHEMA_PATH = path.join(SCHEMA_DIR, SCHEMA_FNAME)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_detector(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    assert sigmf_validate(acquisition.metadata)
    # FIXME: update schema so that this passes
    # schema_validate(sigmf_metadata, schema)
    os.remove(acquisition.data.path)


def test_data_file_created(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    assert acquisition.data
    assert path.exists(acquisition.data.path)
    os.remove(acquisition.data.path)


def test_metadata_single_acquisition(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    assert sigmf_validate(acquisition.metadata)
    check_metadata_fields(acquisition, entry_name, SINGLE_FREQUENCY_FFT_ACQUISITION)


def test_metadata_multiple_acquisition(admin_client, test_scheduler):
    entry_name = simulate_frequency_fft_acquisitions(admin_client, n=2)
    task_results = TaskResult.objects.filter(schedule_entry__name=entry_name)
    for task_result in task_results:
        acquisition = Acquisition.objects.get(task_result=task_result)
        assert sigmf_validate(acquisition.metadata)
        check_metadata_fields(
            acquisition, entry_name, MULTIPLE_FREQUENCY_FFT_ACQUISITIONS
        )
