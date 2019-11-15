import json
import os
from os import path

from django.conf import settings
from sigmf.validate import validate as sigmf_validate

from tasks.models import Acquisition, TaskResult
from tasks.tests.utils import simulate_acquisitions

SCHEMA_DIR = path.join(settings.REPO_ROOT, "schemas")
SCHEMA_FNAME = "scos_transfer_spec_schema.json"
SCHEMA_PATH = path.join(SCHEMA_DIR, SCHEMA_FNAME)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_metadata(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, action="mock_scanned_acquire")
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    assert sigmf_validate(acquisition.metadata)
    # FIXME: update schema so that this passes
    # schema_validate(sigmf_metadata, schema)

    # Check SigMF indexing
    next_freq_domain_annot_start = 0
    next_sensor_annot_start = 0
    next_calibration_annot_start = 0
    sub_fft_size = 0  # Save this value for captures
    for annotation in acquisition.metadata["annotations"]:
        if annotation["ntia-core:annotation_type"] == "FrequencyDomainDetection":
            assert annotation["core:sample_start"] == next_freq_domain_annot_start
            next_freq_domain_annot_start += annotation["core:sample_count"]
        if annotation["ntia-core:annotation_type"] == "SensorAnnotation":
            assert annotation["core:sample_start"] == next_sensor_annot_start
            next_sensor_annot_start += annotation["core:sample_count"]
            sub_fft_size = annotation["core:sample_count"]
        if annotation["ntia-core:annotation_type"] == "CalibrationAnnotation":
            assert annotation["core:sample_start"] == next_calibration_annot_start
            next_calibration_annot_start += annotation["core:sample_count"]
    next_capture_start = 0
    for capture in acquisition.metadata["captures"]:
        assert capture["core:sample_start"] == next_capture_start
        next_capture_start += sub_fft_size


def test_data_file_created(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, action="mock_scanned_acquire")
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    assert acquisition.data
    assert path.exists(acquisition.data.path)
    os.remove(acquisition.data.path)


def test_frequency_selection(user_client, test_scheduler):
    entry_name = simulate_acquisitions(user_client, action="mock_scanned_acquire")
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    # Currently no where to put/check the frequency
    assert False
