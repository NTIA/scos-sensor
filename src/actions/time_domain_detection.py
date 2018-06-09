"""Take an acquisition."""

from __future__ import absolute_import

import logging
from itertools import compress

import numpy as np
from enum import Enum

from rest_framework.reverse import reverse
from sigmf.sigmffile import SigMFFile

from capabilities.models import SensorDefinition
from capabilities.serializers import SensorDefinitionSerializer
from sensor import V1, settings, utils

from .base import Action
from . import usrp


logger = logging.getLogger(__name__)


GLOBAL_INFO = {
    "core:datatype": "f32_le",  # 32-bit float, Little Endian
    "core:version": "0.0.1"
}


# FIXME: comes from initial amplitude accuracy calibration
scale_factor = 1.0

# FIXME: this needs to be defined globally somewhere
SCOS_TRANSFER_SPEC_VER = '0.1'


def calculate_mean_power(array):
    """Calculate mean power of complex time series.

    :param array: a complex time series of n samples
    :returns: mean of modulus squared

    """
    mean_power = np.mean(abs(array)**2)

    return mean_power


class TimeDomainDetection(Action):
    """Perform calculations on complex time series.

    :param frequency: requested center frequency in Hz
    :param sample_rate: requested sample_rate in Hz

    """
    def __init__(self, frequency, sample_rate):
        super(TimeDomainDetection, self).__init__()

        self.frequency = frequency
        self.sample_rate = sample_rate
        self.usrp = usrp  # make instance variable to allow hotswapping mock

    def __call__(self, schedule_entry_name, task_id):
        from schedule.models import ScheduleEntry

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        self.test_required_components()
        self.configure_usrp()
        data = self.acquire_data(parent_entry, task_id)
        detector_data = self.apply_detector(data)
        sigmf_md = self.build_sigmf_md()
        self.archive(mean_power_data, sigmf_md, parent_entry, task_id)

        kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}
        kws.update(V1)
        detail = reverse(
            'acquisition-detail',
            kwargs=kws,
            request=parent_entry.request
        )

        return detail

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        if self.usrp.driver_is_available and not self.usrp.is_available:
            self.usrp.connect()

        required_components = (
            self.usrp.driver_is_available,
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
        msg = "Acquiring {} complex times series at {} MHz"
        
        # FIXME: self.number_of_samples is from new sigmf-ns-scos TimeDomainDetection object 

        logger.debug(msg.format(self.number_of_samples, self.frequency / 1e6))

        data = self.usrp.radio.acquire_samples(self.number_of_samples)

        return data

    def build_sigmf_md(self):
        logger.debug("Building SigMF metadata file")

        sigmf_md = SigMFFile()
        sigmf_md.set_global_field("core:datatype", "rf32_le")
        sigmf_md.set_global_field("core:sample_rate", self.sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        sensor_def_obj = SensorDefinition.objects.get()
        sensor_def_json = SensorDefinitionSerializer(sensor_def_obj).data
        sigmf_md.set_global_field("scos:sensor_definition", sensor_def_json)

        try:
            fqdn = settings.ALLOWED_HOSTS[1]
        except IndexError:
            fqdn = 'not.set'

        sigmf_md.set_global_field("scos:sensor_id", fqdn)
        sigmf_md.set_global_field("scos:version", SCOS_TRANSFER_SPEC_VER)

        capture_md = {
            "core:frequency": self.frequency,
            "core:time": utils.get_datetime_str_now()
        }

        sigmf_md.add_capture(start_index=0, metadata=capture_md)

        time_domain_detection_md = {
            "detector": self.detector,
            "number_of_samples": self.number_of_samples,
            "units": "dBm",
            "reference": "receiver input"
        }

        annotation_md = {
            "scos:measurement_type": {
                "time_domain_detection": time_domain_detection_md,
            }
        }


        sigmf_md.add_annotation(1, metadata=annotation_md)

        return sigmf_md

    def apply_detector(self, data):
        """Apply detector and translate watts to dBm."""
        logger.debug("Applying detector")

        impedance = 50.0  # ohms

        # Apply voltage scale factor
        data_scaled = data * scale_factor

        if self.detector == "mean_power" {
            # Calculate mean power
            mean_power_watts = calculate_mean_power(tdata_scaled) / impedance
            detector_data = 10 * np.log10(mean_powerr_watts) + 30
        }

        return detector_data

    def archive(self, detector_data, sigmf_md, parent_entry, task_id):
        from acquisitions.models import Acquisition

        logger.debug("Storing acquisition in database")

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=detector_data
        ).save()

    @property
    def description(self):
        return """Apply detector on m x n-sample complex time series acquired at {:.2f} MHz.

        The radio will use a sample rate of {:.2f} MHz.

        The resulting data is real-valued with units of dBm.

        """.format(
            self.detector,
            self.number_of_samples,
            self.frequency / 1e6,
            self.sample_rate / 1e6
        )
