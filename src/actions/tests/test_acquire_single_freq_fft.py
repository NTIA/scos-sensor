from __future__ import absolute_import

from actions import by_name
from acquisitions.models import Acquisition
from django.conf import settings
from jsonschema import validate as schema_validate
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sigmf.validate import validate as sigmf_validate

import json
import os

SCHEMA_PATH = os.path.join(settings.REPO_ROOT,
                           "config",
                           "scos_transfer_spec_schema.json")
with open(SCHEMA_PATH, "r") as f:
    schema = json.load(f)


def test_detector(user_client):
    # Put an entry in the schedule that we can refer to
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    task_id = rjson['next_task_id']

    # use mock_acquire set up in conftest.py
    by_name['mock_acquire'](entry_name, task_id)
    acquistion = Acquisition.objects.get(task_id=task_id)
    sigmf_metadata = acquistion.sigmf_metadata
    assert sigmf_validate(sigmf_metadata)
    schema_validate(sigmf_metadata, schema)
