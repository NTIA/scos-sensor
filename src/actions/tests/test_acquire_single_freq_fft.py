import json
from os import path

from django.conf import settings
# from jsonschema import validate as schema_validate
from sigmf.validate import validate as sigmf_validate

import actions
from schedule.tests.utils import post_schedule, TEST_SCHEDULE_ENTRY
from tasks.models import Acquisition


SCHEMA_DIR = path.join(settings.REPO_ROOT, "schemas")
SCHEMA_FNAME = "scos_transfer_spec_schema.json"
SCHEMA_PATH = path.join(SCHEMA_DIR, SCHEMA_FNAME)

with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_detector(user_client, rf):
    # Put an entry in the schedule that we can refer to
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    task_id = rjson['next_task_id']

    # use mock_acquire set up in conftest.py
    actions.by_name['mock_acquire'](entry_name, task_id)
    acquistion = Acquisition.objects.get(task_id=task_id)
    sigmf_metadata = acquistion.sigmf_metadata
    assert sigmf_validate(sigmf_metadata)
    # FIXME: update schema so that this passes
    # schema_validate(sigmf_metadata, schema)
