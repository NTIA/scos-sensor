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
from capabilities import (scos_antenna_obj,
                          data_extract_obj,
                          SCOS_TRANSFER_SPEC_VER)

import os

logger = logging.getLogger(__name__)


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}


SIGMF_DATETIME_ISO8601_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


class M4sDetector(Enum):
    min = 1
    max = 2
    mean = 3
    median = 4
    sample = 5


def get_sigmf_iso8601_datetime_now():
    return datetime.isoformat(datetime.utcnow()) + 'Z'


def parse_iso8601_datetime(d):
    return datetime.strptime(d, SIGMF_DATETIME_ISO8601_FMT)


# FIXME: comes from initial amplitude accuracy calibration
scale_factor = 1.0


def m4s_detector(array):
    """Take min, max, mean, median, and random sample of n-dimensional array.

    Detector is applied along each column.

    :param array: an (m x n) array of real frequency-domain linear power values
    :returns: a (5 x n) in the order min, max, mean, median, sample in the case
              that `detector` is `m4s`, otherwise a (1 x n) array

    """
    amin = np.min(array, axis=0)
    amax = np.max(array, axis=0)
    mean = np.mean(array, axis=0)
    median = np.median(array, axis=0)
    random_sample = array[np.random.randint(0, array.shape[0], 1)][0]
    m4s = np.array(
        [amin, amax, mean, median, random_sample], dtype=np.float32)

    return m4s


class SingleFrequencyFftAcquisition(Action):
    """Perform m4s detection over requested number of single-frequency FFTs.

    :param frequency: center frequency in Hz
    :param sample_rate: requested sample_rate in Hz
    :param fft_size: number of points in FFT (some 2^n)
    :param nffts: number of consecutive FFTs to pass to detector

    """
    def __init__(self, frequency, sample_rate, fft_size, nffts):
        super(SingleFrequencyFftAcquisition, self).__init__()

        self.frequency = frequency
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.nffts = nffts
        self.usrp = usrp  # make instance variable to allow hotswapping mock
        self.enbw = None

    def __call__(self, schedule_entry_name, task_id):
        from schedule.models import ScheduleEntry

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        self.test_required_components()
        self.configure_usrp()
        data = self.acquire_data(parent_entry, task_id)
        m4s_data = self.apply_detector(data)
        sigmf_md = self.build_sigmf_md()
        self.archive(m4s_data, sigmf_md, parent_entry, task_id)

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        if self.usrp.uhd_is_available and not self.usrp.is_available:
            self.usrp.connect()

        required_components = (
            self.usrp.uhd_is_available,
            self.usrp.is_available
        )
        component_names = ("UHD", "USRP")
        missing_components = [not rc for rc in required_components]
        if any(missing_components):
            missing = tuple(compress(component_names, missing_components))
            msg = "acquisition failed: {} required but not available"
            raise RuntimeError(msg.format(missing))

    def configure_usrp(self):
        self.set_usrp_clock_rate()
        self.set_usrp_sample_rate()
        self.set_usrp_frequency()

    def set_usrp_sample_rate(self):
        self.usrp.radio.sample_rate = self.sample_rate
        self.sample_rate = self.usrp.radio.sample_rate

    def set_usrp_clock_rate(self):
        clock_rate = self.sample_rate
        while clock_rate < 10e6:
            clock_rate *= 4

        self.usrp.radio.clock_rate = clock_rate

    def set_usrp_frequency(self):
        requested_frequency = self.frequency
        self.usrp.radio.frequency = requested_frequency
        self.frequency = self.usrp.radio.frequency

    def acquire_data(self, parent_entry, task_id):
        msg = "Acquiring {} FFTs at {} MHz"
        logger.debug(msg.format(self.nffts, self.frequency / 1e6))

        data = self.usrp.radio.acquire_samples(self.nffts * self.fft_size)
        data.resize((self.nffts, self.fft_size))

        return data

    def build_sigmf_md(self):
        logger.debug("Building SigMF metadata file")

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", self.sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        sensor_definition = {
            "antenna": scos_antenna_obj["scos:antenna"],
            "data_extraction_unit":
                data_extract_obj["scos:data_extraction_unit"]
        }

        sigmf_md.set_global_field("scos:sensor_definition", sensor_definition)
        domains = os.environ['DOMAINS']
        fqdn = domains.split()[1]
        sigmf_md.set_global_field("scos:sensor_id", fqdn)
        sigmf_md.set_global_field("scos:version", SCOS_TRANSFER_SPEC_VER)

        capture_md = {
            "core:frequency": self.frequency,
            "core:time": get_sigmf_iso8601_datetime_now()
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        for i, detector in enumerate(M4sDetector):
            single_frequency_fft_md = {
                "number_of_samples_in_fft": self.fft_size,
                "window": "blackman",
                "equivalent_noise_bandwidth": self.enbw,
                "detector": detector.name + "_power",
                "number_of_ffts": self.nffts,
                "units": "dBm",
                "reference": "not referenced"
            }

            annotation_md = {
                "scos:measurement_type": {
                        "SingleFrequencyFFTDetection": single_frequency_fft_md
                }
            }

            sigmf_md.add_annotation(
                start_index=(i * self.fft_size),
                length=self.fft_size,
                metadata=annotation_md
            )

        return sigmf_md

    def apply_detector(self, data):
        """Take FFT of data, apply detector, and translate watts to dBm."""
        logger.debug("Applying detector")

        window = np.blackman(self.fft_size)
        window_power = sum(window**2)
        impedance = 50.0  # ohms

        self.enbw = self.fft_size * window_power / sum(window)**2

        Vsq2W_dB = -10.0 * np.log10(self.fft_size * window_power * impedance)

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
        fdata_watts_m4s = m4s_detector(fdata_watts)
        fdata_dbm_m4s = 10 * np.log10(fdata_watts_m4s) + 30 + Vsq2W_dB

        return fdata_dbm_m4s

    def archive(self, m4s_data, sigmf_md, parent_entry, task_id):
        from acquisitions.models import Acquisition

        logger.debug("Storing acquisition in database")

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=m4s_data
        ).save()

    @property
    def description(self):
        return """Apply m4s detector over {} {}-point FFTs at {:.2f} MHz.

        The radio will use a sample rate of {:.2f} MHz.

        The m4s detector will take the min, max, mean, median, and a random
        sample over the requested FFTs.

        The FFTs are taken gap-free in time and a Blackman window is applied.
        The resulting data is real-valued with units of dBm.

        """.format(
            self.nffts,
            self.fft_size,
            self.frequency / 1e6,
            self.sample_rate / 1e6
        )
