import json
import os
from os import path

from django.conf import settings
from sigmf.validate import validate as sigmf_validate


from actions.tests.utils import check_metadata_fields
from tasks.models import Acquisition, TaskResult
from tasks.tests.utils import simulate_multirec_acquisition, SINGLE_TIMEDOMAIN_IQ_MULTI_RECORDING_ACQUISITION, simulate_timedomain_iq_acquisition, SINGLE_TIMEDOMAIN_IQ_ACQUISITION


SCHEMA_DIR = path.join(settings.REPO_ROOT, "schemas")
SCHEMA_FNAME = "scos_transfer_spec_schema.json"
SCHEMA_PATH = path.join(SCHEMA_DIR, SCHEMA_FNAME)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_metadata(user_client, test_scheduler):
    entry_name = simulate_multirec_acquisition(user_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisitions = Acquisition.objects.filter(task_result=tr)
    for acquisition in acquisitions:
        assert sigmf_validate(acquisition.metadata)
        # FIXME: update schema so that this passes
        # schema_validate(sigmf_metadata, schema)


def test_data_file_created(user_client, test_scheduler):
    entry_name = simulate_multirec_acquisition(user_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisitions = Acquisition.objects.filter(task_result=tr)
    for acquisition in acquisitions:
        assert acquisition.data
        assert path.exists(acquisition.data.path)
        os.remove(acquisition.data.path)

def test_metadata_multirecording_acquisition(user_client, test_scheduler):
    entry_name = simulate_multirec_acquisition(user_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisitions = Acquisition.objects.filter(task_result=tr)
    for acquisition in acquisitions:
        check_metadata_fields(acquisition, entry_name, SINGLE_TIMEDOMAIN_IQ_MULTI_RECORDING_ACQUISITION, is_multirecording=True)

def test_metadata_timedomain_iq_single_acquisition(user_client, test_scheduler):
    entry_name = simulate_timedomain_iq_acquisition(user_client)
    tr = TaskResult.objects.get(schedule_entry__name=entry_name, task_id=1)
    acquisition = Acquisition.objects.get(task_result=tr)
    check_metadata_fields(acquisition, entry_name, SINGLE_TIMEDOMAIN_IQ_ACQUISITION, is_multirecording=False)
