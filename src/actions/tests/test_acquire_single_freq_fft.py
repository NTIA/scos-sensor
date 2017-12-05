from __future__ import absolute_import

from actions import acquire_single_freq_fft
from acquisitions.models import Acquisition
from schedule.tests import TEST_SCHEDULE_ENTRY
from schedule.tests.utils import post_schedule
from sigmf.validate import validate

from .mocks import usrp as mock_usrp


def run_single_frequency_fft_acquisition(user_client):
    # Put an entry in the schedule that we can refer to
    rjson = post_schedule(user_client, TEST_SCHEDULE_ENTRY)
    entry_name = rjson['name']
    task_id = rjson['next_task_id']

    # Retreive that actual instance
    action = acquire_single_freq_fft.SingleFrequencyFftAcquisition(
        frequency=400e6,
        sample_rate=10e6,
        fft_size=16,
        nffts=11  # [0.0] * 16 to [1.0] * 16
    )
    action.usrp = mock_usrp
    action(entry_name, task_id)
    return task_id


def test_detector(user_client):
    run_single_frequency_fft_acquisition(user_client)


def test_validate_sigmf_output(user_client):
    task_id = run_single_frequency_fft_acquisition(user_client)
    acquistion = Acquisition.objects.get(task_id=task_id)
    sigmf_metadata = acquistion.sigmf_metadata
    assert validate(sigmf_metadata)
