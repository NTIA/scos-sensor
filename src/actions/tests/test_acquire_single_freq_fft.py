from __future__ import absolute_import

from actions import acquire_single_freq_fft, by_name
from acquisitions.models import Acquisition
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sigmf.validate import validate

from .mocks import usrp as mock_usrp


def test_detector(user_client):
    # Put an entry in the schedule that we can refer to
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    task_id = rjson['next_task_id']

    # use mock_acquire set up in conftest.py
    by_name['mock_acquire'](entry_name, task_id)
    acquistion = Acquisition.objects.get(task_id=task_id)
    sigmf_metadata = acquistion.sigmf_metadata
    assert validate(sigmf_metadata)

