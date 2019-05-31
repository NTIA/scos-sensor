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
r"""Capture time-domain IQ samples at {nfcs} frequencies between
{f_low_edge:.2f} and {f_high_edge:.2f} MHz.

# {name}

## Radio setup and sample acquisition

Each time this task runs, the following process is followed:

{acquisition_plan}

This will take a minimum of {min_duration_ms:.2f} ms, not including radio
tuning, dropping samples after retunes, and data storage.

## Time-domain processing

If specified, a voltage scaling factor is applied to the complex time-domain
signals.

## Data Archive

Each capture will be ${total_samples}\; \text{{samples}} \times 8\;
\text{{bytes per sample}} = {filesize_mb:.2f}\; \text{{MB}}$ plus metadata.

"""

import logging
from itertools import zip_longest

import numpy as np
from sigmf.sigmffile import SigMFFile

from capabilities import capabilities
from hardware import sdr
from sensor import settings, utils

from .base import Action

logger = logging.getLogger(__name__)

GLOBAL_INFO = {
    "core:datatype": "cf32_le",  # 2x 32-bit float, Little Endian
    "core:version": "0.0.2",
}


# The sigmf-ns-scos version targeted by this action
SCOS_TRANSFER_SPEC_VER = "0.2"


class SteppedFrequencyTimeDomainIqAcquisition(Action):
    """Acquire IQ data at each of the requested frequecies.

    :param name: the name of the action
    :param fcs: an iterable of center frequencies in Hz
    :param gains: requested gain in dB, per fc
    :param sample_rates: iterable of sample_rates in Hz, per fc
    :param durations_ms: duration to acquire in ms, per fc

    """

    def __init__(self, name, fcs, gains, sample_rates, durations_ms):
        super(SteppedFrequencyTimeDomainIqAcquisition, self).__init__()

        nfcs = len(fcs)

        parameter_names = ("gain", "sample_rate", "duration_ms")
        tuning_parameters = {}

        for fc, *params in zip_longest(fcs, gains, sample_rates, durations_ms):
            if None in params:
                param_name = parameter_names[params.index(None)]
                err = "Wrong number of {}s, expected {}"
                raise TypeError(err.format(param_name, nfcs))

            tuning_parameters[fc] = dict(zip(parameter_names, params))

        self.name = name
        self.nfcs = nfcs
        self.fcs = fcs
        self.tuning_parameters = tuning_parameters
        self.sdr = sdr  # make instance variable to allow mocking

    def __call__(self, schedule_entry_name, task_id):
        """This is the entrypoint function called by the scheduler."""
        from tasks.models import TaskResult

        # Raises TaskResult.DoesNotExist if no matching task result
        task_result = TaskResult.objects.get(
            schedule_entry__name=schedule_entry_name, task_id=task_id
        )

        self.test_required_components()

        for recording_id, fc in enumerate(self.fcs, start=1):
            data, sigmf_md = self.acquire_data(fc)
            self.archive(task_result, data, sigmf_md, recording_id)

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        self.sdr.connect()
        if not self.sdr.is_available:
            msg = "acquisition failed: SDR required but not available"
            raise RuntimeError(msg)

    def acquire_data(self, fc):
        tuning_parameters = self.tuning_parameters[fc]
        self.configure_sdr(fc, **tuning_parameters)

        # Use the radio's actual reported sample rate instead of requested rate
        sample_rate = self.sdr.radio.sample_rate

        # Build global metadata
        sigmf_md = SigMFFile()
        sigmf_md.set_global_info(GLOBAL_INFO)
        sigmf_md.set_global_field("core:sample_rate", sample_rate)
        sigmf_md.set_global_field("core:description", self.description)

        sensor_def = capabilities["sensor_definition"]
        sigmf_md.set_global_field("ntia:sensor_definition", sensor_def)
        sigmf_md.set_global_field("ntia:sensor_id", settings.FQDN)
        sigmf_md.set_global_field("scos:version", SCOS_TRANSFER_SPEC_VER)

        # Acquire data and build per-capture metadata
        data = np.array([], dtype=np.complex64)

        nsamps = int(sample_rate * tuning_parameters["duration_ms"] * 1e-3)

        dt = utils.get_datetime_str_now()
        acq = self.sdr.radio.acquire_samples(nsamps).astype(np.complex64)
        data = np.append(data, acq)
        capture_md = {"core:frequency": fc, "core:datetime": dt}
        sigmf_md.add_capture(start_index=0, metadata=capture_md)
        annotation_md = {"applied_scale_factor": self.sdr.radio.scale_factor}
        sigmf_md.add_annotation(start_index=0, length=nsamps, metadata=annotation_md)

        return data, sigmf_md

    def configure_sdr(self, fc, gain, sample_rate, duration_ms):
        self.set_sdr_clock_rate(sample_rate)
        self.set_sdr_sample_rate(sample_rate)
        self.sdr.radio.tune_frequency(fc)
        self.sdr.radio.gain = gain

    def set_sdr_clock_rate(self, sample_rate):
        clock_rate = sample_rate
        while clock_rate < 10e6:
            clock_rate *= 4

        self.sdr.radio.clock_rate = clock_rate

    def set_sdr_sample_rate(self, sample_rate):
        self.sdr.radio.sample_rate = sample_rate

    def archive(self, task_result, m4s_data, sigmf_md):
        from tasks.models import Acquisition

        logger.debug("Storing acquisition in database")

        Acquisition(
            task_result=task_result, metadata=sigmf_md._metadata, data=m4s_data
        ).save()

    @property
    def description(self):
        """Parameterize and return the module-level docstring."""

        acquisition_plan = ""
        acq_plan_template = "1. Tune to {fc_MHz:.2f} MHz, "
        acq_plan_template += "set gain to {gain} dB, "
        acq_plan_template += "and acquire at {sample_rate_Msps:.2f} Msps "
        acq_plan_template += "for {duration_ms} ms\n"

        total_samples = 0
        for fc in self.fcs:
            tuning_params = self.tuning_parameters[fc].copy()
            tuning_params["fc_MHz"] = fc / 1e6
            srate = tuning_params["sample_rate"]
            tuning_params["sample_rate_Msps"] = srate / 1e6
            acquisition_plan += acq_plan_template.format(**tuning_params)
            total_samples += int(tuning_params["duration_ms"] / 1e6 * srate)

        f_low = self.fcs[0]
        f_low_srate = self.tuning_parameters[f_low]["sample_rate"]
        f_low_edge = (f_low - f_low_srate / 2.0) / 1e6

        f_high = self.fcs[-1]
        f_high_srate = self.tuning_parameters[f_high]["sample_rate"]
        f_high_edge = (f_high - f_high_srate / 2.0) / 1e6

        durations = [v["duration_ms"] for v in self.tuning_parameters.values()]
        min_duration_ms = np.sum(durations)

        filesize_mb = total_samples * 8 / 1e6  # 8 bytes per complex64 sample

        defs = {
            "name": self.name,
            "nfcs": self.nfcs,
            "f_low_edge": f_low_edge,
            "f_high_edge": f_high_edge,
            "acquisition_plan": acquisition_plan,
            "min_duration_ms": min_duration_ms,
            "total_samples": total_samples,
            "filesize_mb": filesize_mb,
        }

        # __doc__ refers to the module docstring at the top of the file
        return __doc__.format(**defs)
