"""Take an acquisition."""

import logging
from datetime import datetime

import numpy as np

from sigmf.sigmffile import SigMFFile

from .base import Action


logger = logging.getLogger(__name__)


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}


SIGMF_DATETIME_ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def get_sigmf_iso8601_datetime_now():
    return datetime.isoformat(datetime.utcnow()) + 'Z'


def parse_iso8601_datetime(d):
    return datetime.strptime(d, SIGMF_DATETIME_ISO8601_FMT)


TEST_DATA_SHA512 = ("62171ba5e622232987f367c6f3cea85d"
                    "116a88a2e385dd07b54dc0dcd04c74da"
                    "f8027f7993af8356ea29ad6c64818bda"
                    "f2c5beb89efc0f8bc2c7838268535cda")


class TestAcquisition(Action):
    """Test an acquisition without using the radio."""
    def __call__(self, schedule_entry_name, task_id):
        from acquisitions.models import Acquisition
        from schedule.models import ScheduleEntry

        frequency = 700e6
        sample_rate = 10e6
        fft_size = 1024
        nffts = 1
        detector = 'mean'  # TODO: enum

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", sample_rate)
        description = "test acquisition {}/{}".format(schedule_entry_name,
                                                      task_id)
        sigmf_md.set_global_field("core:description", description)

        data = np.arange(fft_size, dtype=np.float32).tobytes()

        capture_md = {
            "core:frequency": frequency,
            "core:time": get_sigmf_iso8601_datetime_now()
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        annotation_md = {
            "core:latitude": 40.0,
            "core:longitude": -105.0,
            "scos:detector": detector
        }

        sigmf_md.add_annotation(start_index=0,
                                length=fft_size,
                                metadata=annotation_md)

        logger.info("running test acquisition")

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=data
        ).save()
