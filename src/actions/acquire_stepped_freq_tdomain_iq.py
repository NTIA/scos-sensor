# What follows is a parameterizable description of the algorithm used by this
# action. The first line is the summary and should be written in plain text.
# Everything following that is the extended description, which can be written
# in Markdown and MathJax. Each name in curly brackets '{}' will be replaced
# with the value specified in the `description` method which can be found at
# the very bottom of this file. Since this parameterization step affects
# everything in curly brackets, math notation such as {m \over n} must be
# escaped to {{m \over n}}.
#
# To print out this docstring after parameterization, see
# REPO_ROOT/scripts/print_action_docstring.py. You can then paste that into the
# SCOS Markdown Editor (link below) to see the final rendering.
#
# Resources:
# - MathJax reference: https://math.meta.stackexchange.com/q/5020
# - Markdown reference: https://commonmark.org/help/
# - SCOS Markdown Editor: https://ntia.github.io/scos-md-editor/
#
r"""Capture time-domain IQ samples at {sample_rate:.2f} Msps for {duration_ms}
ms in {nfcs} steps between {f_low:.2f} and {f_high:.2f} MHz.

# {name}

## Radio setup and sample acquisition

The following procedure happens at each frequency in {fcs} Hz.

This action tunes to a center frequency, requests a sample rate of
{sample_rate:.2f} Msps and {gain} dB of gain.

It then begins acquiring, and discards an appropriate number of samples while
the radio's IQ balance algorithm runs. Then, samples are streamed from the
radio for {duration_ms} ms.

## Time-domain processing

If specified, a voltage scaling factor is applied to the complex time-domain
signals.

## Data Archive

Each capture will contain $\lfloor {sample_rate:.2f}\; \text{{Msps}} \times
{duration_ms}\; \text{{ms}} \rfloor = {nsamples}\; \text{{samples}}$.

Each capture will be ${nsamples}\; \text{{samples}} \times 8\; \text{{bytes per
sample}} \times {nfcs}\; \text{{frequencies}} = {filesize_mb:.2f}\;
\text{{MB}}$ plus metadata.

"""

from __future__ import absolute_import

import logging

import numpy as np

from rest_framework.reverse import reverse
from sigmf.sigmffile import SigMFFile

from capabilities.models import SensorDefinition
from capabilities.serializers import SensorDefinitionSerializer
from hardware import usrp_iface
from sensor import V1, settings, utils

from .base import Action

logger = logging.getLogger(__name__)

GLOBAL_INFO = {
    "core:datatype": "cf32_le",  # 2x 32-bit float, Little Endian
    "core:version": "0.0.1"
}


# The sigmf-ns-scos version targeted by this action
SCOS_TRANSFER_SPEC_VER = '0.2'


class SteppedFrequencyTimeDomainIq(Action):
    """Acquire IQ data at each of the requested frequecies.

    :param name: the name of the action
    :param fcs: an iterable of center frequencies in Hz
    :param gain: requested gain in dB
    :param sample_rate: requested sample_rate in Hz
    :param duration_ms: duration to acquire at each center frequency in ms

    """

    def __init__(self, name, fcs, gain, sample_rate, duration_ms):
        super(SteppedFrequencyTimeDomainIq, self).__init__()

        self.name = name
        self.fcs = sorted(fcs)
        self.gain = gain
        self.sample_rate = sample_rate
        self.duration_ms = duration_ms
        self.nsamples = int(sample_rate * duration_ms * 1e-3)
        self.usrp = usrp_iface  # make instance variable to allow mocking

    def __call__(self, schedule_entry_name, task_id):
        """This is the entrypoint function called by the scheduler."""
        from schedule.models import ScheduleEntry

        # raises ScheduleEntry.DoesNotExist if no matching schedule entry
        parent_entry = ScheduleEntry.objects.get(name=schedule_entry_name)

        self.test_required_components()
        self.configure_usrp()
        data, sigmf_md = self.acquire_data(parent_entry, task_id)
        self.archive(data, sigmf_md, parent_entry, task_id)

        kws = {'schedule_entry_name': schedule_entry_name, 'task_id': task_id}
        kws.update(V1)
        detail = reverse(
            'acquisition-detail', kwargs=kws, request=parent_entry.request)

        return detail

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        self.usrp.connect()
        if not self.usrp.is_available:
            msg = "acquisition failed: USRP required but not available"
            raise RuntimeError(msg)

    def configure_usrp(self):
        self.set_usrp_clock_rate()
        self.set_usrp_sample_rate()
        self.usrp.radio.tune_frequency(self.fcs[0])
        self.usrp.radio.gain = self.gain

    def set_usrp_sample_rate(self):
        self.usrp.radio.sample_rate = self.sample_rate
        self.sample_rate = self.usrp.radio.sample_rate

    def set_usrp_clock_rate(self):
        clock_rate = self.sample_rate
        while clock_rate < 10e6:
            clock_rate *= 4

        self.usrp.radio.clock_rate = clock_rate

    def acquire_data(self, parent_entry, task_id):
        # Build global metadata
        sigmf_md = SigMFFile()
        sigmf_md.set_global_info(GLOBAL_INFO)
        sigmf_md.set_global_field("core:sample_rate", self.sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        try:
            sensor_def_obj = SensorDefinition.objects.get()
            sensor_def = SensorDefinitionSerializer(sensor_def_obj).data
            sigmf_md.set_global_field("scos:sensor_definition", sensor_def)
        except SensorDefinition.DoesNotExist:
            pass

        try:
            fqdn = settings.ALLOWED_HOSTS[1]
        except IndexError:
            fqdn = 'not.set'

        sigmf_md.set_global_field("scos:sensor_id", fqdn)
        sigmf_md.set_global_field("scos:version", SCOS_TRANSFER_SPEC_VER)

        # Acquire data and build per-capture metadata
        data = np.array([], dtype=np.complex64)
        nsamps = self.nsamples

        for idx, fc in enumerate(self.fcs):
            self.usrp.radio.tune_frequency(fc)
            dt = utils.get_datetime_str_now()
            acq = self.usrp.radio.acquire_samples(nsamps).astype(np.complex64)
            data = np.append(data, acq)
            start_idx = idx * nsamps
            capture_md = {"core:frequency": fc, "core:datetime": dt}
            sigmf_md.add_capture(start_index=start_idx, metadata=capture_md)
            annotation_md = {
                "applied_scale_factor": self.usrp.radio.scale_factor
            }
            sigmf_md.add_annotation(start_index=start_idx, length=nsamps,
                                    metadata=annotation_md)

        return data, sigmf_md

    def archive(self, m4s_data, sigmf_md, parent_entry, task_id):
        from acquisitions.models import Acquisition

        logger.debug("Storing acquisition in database")

        Acquisition(
            schedule_entry=parent_entry,
            task_id=task_id,
            sigmf_metadata=sigmf_md._metadata,
            data=m4s_data).save()

    @property
    def description(self):
        defs = {
            'name': self.name,
            'fcs': self.fcs,
            'f_low': (self.fcs[0] - self.sample_rate / 2.0) / 1e6,
            'f_high': (self.fcs[-1] + self.sample_rate / 2.0) / 1e6,
            'nfcs': len(self.fcs),
            'sample_rate': self.sample_rate / 1e6,
            'duration_ms': self.duration_ms,
            'nsamples': self.nsamples,
            'gain': self.gain,
            'filesize_mb': self.nsamples * 8 * len(self.fcs) * 1e-6
        }

        # __doc__ refers to the module docstring at the top of the file
        return __doc__.format(**defs)
