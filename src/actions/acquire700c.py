"""Take an acquisition."""

from __future__ import absolute_import

import logging
from datetime import datetime
from itertools import compress

import numpy as np
from enum import Enum

from sigmf.sigmffile import SigMFFile

from .base import Action
from . import usrp


logger = logging.getLogger(__name__)


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}


SIGMF_DATETIME_ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


class Detector(Enum):
    min = 1
    max = 2
    mean = 3
    median = 4
    m4s = 5  # The above 4 detectors plus one sample of the inputs at random


def get_sigmf_iso8601_datetime_now():
    return datetime.isoformat(datetime.utcnow()) + 'Z'


def parse_iso8601_datetime(d):
    return datetime.strptime(d, SIGMF_DATETIME_ISO8601_FMT)


# FIXME: comes from initial amplitude accuracy calibration
scale_factor = 1.0


def apply_detector(array, detector):
    """Detect the min, max, mean, and/or median of a multi-dimentional array.

    Detector is applied along each column.

    Example usage:
        >>> a = np.array([[0, 0],
        ...               [1, 1]])
        >>> apply_detector(a, Detector.max)
        array([1,  1])

    :param array: an (m x n) array of real frequency-domain linear power values
    :param detector: a :class:`Detector` enum value
    :returns: a (5 x n) in the order min, max, mean, median, sample in the case
              that `detector` is `m4s`, otherwise a (1 x n) array

    """
    nffts, fft_size = array.shape

    if detector in {Detector.min, Detector.m4s}:
        amin = np.min(array, axis=0)
        if detector is Detector.min:
            return amin

    if detector in {Detector.max, Detector.m4s}:
        amax = np.max(array, axis=0)
        if detector is Detector.max:
            return amax

    if detector in {Detector.mean, Detector.m4s}:
        mean = np.mean(array, axis=0)
        if detector is Detector.mean:
            return mean

    if detector in {Detector.median, Detector.m4s}:
        median = np.median(array, axis=0)
        if detector is Detector.median:
            return median

    if detector is detector.m4s:
        random_sample = array[np.random.randint(0, array.shape[0], 1)][0]
        m4s = np.array([amin, amax, mean, median, random_sample])
        return m4s

    raise NotImplementedError("Unknown detector: {}".format(detector))


class LTE700cAcquisition(Action):
    """Acquire 700c LTE band (751 MHz center frequency)."""
    def __call__(self, schedule_entry_name, task_id):
        from acquisitions.models import Acquisition
        from schedule.models import ScheduleEntry

        required_components = (usrp.uhd_is_available, usrp.is_available,)
        component_names = ("UHD", "USRP")
        missing_components = (not rc for rc in required_components)
        if any(missing_components):
            missing = tuple(compress(component_names, missing_components))
            msg = "acquisition failed: {} required but not available"
            raise RuntimeError(msg.format(missing))

        frequency_Hz = 751e6
        frequency_MHz = frequency_Hz / 1e6
        clock_rate = 15.36e6
        sample_rate = clock_rate
        fft_size = 1024
        nffts = 30
        detector = Detector.m4s

        logger.debug("tuning USRP to {} MHz".format(frequency_MHz))

        # set USRP with desired parameters
        usrp.radio.frequency = frequency_Hz
        usrp.radio.clock_rate = clock_rate
        usrp.radio.sample_rate = sample_rate

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        logger.info("acquiring {} FFTs at {} MHz".format(nffts, frequency_MHz))

        window = np.blackman(fft_size)
        window_power = sum(tap*tap for tap in window)
        impedance = 50.0  # ohms
        Vsq2W_dB = -10.0 * np.log10(fft_size * window_power * impedance)

        capture_md = {
            "core:frequency": frequency_Hz,
            "core:time": get_sigmf_iso8601_datetime_now()
        }

        data = usrp.radio.finite_acquisition(nffts * fft_size)
        data.resize((nffts, fft_size))

        # Apply voltage scale factor
        tdata_scaled = data * scale_factor
        # Apply window
        tdata_windowed = tdata_scaled * window
        # Take FFT
        fdata = np.fft.fft(tdata_windowed)
        # Shift fc to center
        fdata_shifted = np.fft.fftshift(fdata)
        # Take power
        fdata_watts = np.square(np.abs(fdata_shifted))
        # Apply detector while we're linear
        # The m4s detector returns a (5 x fft_size) ndarray
        fdata_watts_m4s = apply_detector(fdata_watts, detector)
        fdata_dbm_m4s = 10 * np.log10(fdata_watts_m4s) + 30 + Vsq2W_dB

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        for i, d in enumerate(Detector):
            annotation_md = {
                "core:latitude": 40.0,
                "core:longitude": -105.0,
                "scos:detector": d.name
            }

            sigmf_md.add_annotation(start_index=i * fft_size,
                                    length=fft_size,
                                    metadata=annotation_md)

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=fdata_dbm_m4s
        ).save()
