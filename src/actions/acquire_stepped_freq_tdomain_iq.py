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
r"""Capture time-domain IQ samples at the following {num_center_frequencies} frequencies: {center_frequencies}.

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
from django.core.files.base import ContentFile
from sigmf.sigmffile import SigMFFile

from actions.measurement_params import MeasurementParams
from capabilities import capabilities
from hardware import sdr
from sensor import settings, utils
from status.utils import get_location

from .base import Action

logger = logging.getLogger(__name__)

GLOBAL_INFO = {
    "core:datatype": "cf32_le",  # 2x 32-bit float, Little Endian
    "core:version": "0.0.2",
}


class SteppedFrequencyTimeDomainIqAcquisition(Action):
    """Acquire IQ data at each of the requested frequecies.

    :param name: the name of the action
    :param fcs: an iterable of center frequencies in Hz
    :param gains: requested gain in dB, per center_frequency
    :param sample_rates: iterable of sample_rates in Hz, per center_frequency
    :param durations_ms: duration to acquire in ms, per center_frequency

    """

    def __init__(self, name, fcs, gains, sample_rates, durations_ms):
        super(SteppedFrequencyTimeDomainIqAcquisition, self).__init__()

        num_center_frequencies = len(fcs)

        parameter_names = ("center_frequency", "gain", "sample_rate", "duration_ms")
        measurement_params_list = []

        # Sort combined parameter list by frequency
        def sortFrequency(zipped_params):
            return zipped_params[0]

        sorted_params = list(zip_longest(fcs, gains, sample_rates, durations_ms))
        sorted_params.sort(key=sortFrequency)

        for params in sorted_params:
            if None in params:
                param_name = parameter_names[params.index(None)]
                err = "Wrong number of {}s, expected {}"
                raise TypeError(err.format(param_name, num_center_frequencies))

            measurement_params_list.append(
                MeasurementParams(**dict(zip(parameter_names, params)))
            )

        self.name = name
        self.num_center_frequencies = num_center_frequencies
        self.measurement_params_list = measurement_params_list
        self.sdr = sdr  # make instance variable to allow mocking

    def __call__(self, schedule_entry_name, task_id):
        """This is the entrypoint function called by the scheduler."""
        from tasks.models import TaskResult

        # Raises TaskResult.DoesNotExist if no matching task result
        task_result = TaskResult.objects.get(
            schedule_entry__name=schedule_entry_name, task_id=task_id
        )

        self.test_required_components()

        for recording_id, measurement_params in enumerate(
            self.measurement_params_list, start=1
        ):
            start_time = utils.get_datetime_str_now()
            data = self.acquire_data(measurement_params, task_id)
            end_time = utils.get_datetime_str_now()
            sigmf_md = self.build_sigmf_md(
                task_id,
                measurement_params,
                data,
                task_result.schedule_entry,
                recording_id,
                start_time,
                end_time
            )
            self.archive(task_result, recording_id, data, sigmf_md)

    @property
    def is_multirecording(self):
        return len(self.measurement_params_list) > 1

    def test_required_components(self):
        """Fail acquisition if a required component is not available."""
        self.sdr.connect()
        if not self.sdr.is_available:
            msg = "acquisition failed: SDR required but not available"
            raise RuntimeError(msg)

    def acquire_data(self, measurement_params, task_id):
        self.configure_sdr(measurement_params)

        # Use the radio's actual reported sample rate instead of requested rate
        sample_rate = self.sdr.radio.sample_rate

        # Acquire data and build per-capture metadata
        data = np.array([], dtype=np.complex64)

        num_samples = measurement_params.get_num_samples()

        # Drop ~10 ms of samples
        nskip = int(0.01 * sample_rate)
        acq = self.sdr.radio.acquire_samples(num_samples, nskip=nskip).astype(
            np.complex64
        )
        data = np.append(data, acq)

        return data

    def build_sigmf_md(
        self, task_id, measurement_params, data, schedule_entry, recording_id, start_time, end_time
    ):
        # Build global metadata
        sigmf_md = SigMFFile()
        sigmf_md.set_global_info(
            GLOBAL_INFO.copy()
        )  # prevent GLOBAL_INFO from being modified by sigmf
        sample_rate = self.sdr.radio.sample_rate
        sigmf_md.set_global_field("core:sample_rate", sample_rate)

        measurement_object = {
            "start_time": start_time,
            "end_time": end_time,
            "domain": "Time",
            "measurement_type": "survey" if self.is_multirecording else "single-frequency"
        }
        frequencies = self.get_frequencies(data, measurement_params)
        measurement_object['low_frequency'] = frequencies[0]
        measurement_object['high_frequency'] = frequencies[-1]
        sigmf_md.set_global_field("ntia-core:measurement", measurement_object)

        sensor = capabilities["sensor"]
        sensor["id"] = settings.FQDN
        sigmf_md.set_global_field("ntia-sensor:sensor", sensor)
        from status.views import get_last_calibration_time
        sigmf_md.set_global_field("ntia-sensor:calibration_datetime", get_last_calibration_time())

        action_def = {
            "name": self.name,
            "description": self.description,
            "summary": self.description.splitlines()[0]
        }

        sigmf_md.set_global_field("ntia-scos:action", action_def)
        #sigmf_md.set_global_field("ntia-scos:task_id", task_id)
        if self.is_multirecording:
            sigmf_md.set_global_field("ntia-scos:recording", recording_id)

        sigmf_md.set_global_field("ntia-scos:task", task_id)

        from schedule.serializers import ScheduleEntrySerializer

        serializer = ScheduleEntrySerializer(
            schedule_entry, context={"request": schedule_entry.request}
        )
        schedule_entry_json = serializer.to_sigmf_json()
        schedule_entry_json['id'] = schedule_entry.name
        sigmf_md.set_global_field("ntia-scos:schedule", schedule_entry_json)

        dt = utils.get_datetime_str_now()

        num_samples = measurement_params.get_num_samples()

        capture_md = {"core:frequency": self.sdr.radio.frequency, "core:datetime": dt}
        sigmf_md.add_capture(start_index=0, metadata=capture_md)
        calibration_annotation_md = self.sdr.radio.create_calibration_annotation()
        sigmf_md.add_annotation(
            start_index=0, length=num_samples, metadata=calibration_annotation_md
        )

        # time = range(0, (num_samples-1)*(1/sample_rate), (1/sample_rate))
        time = np.linspace(0, (1/sample_rate)*num_samples, num=num_samples, endpoint=False)

        time_domain_detection_md = {
            "ntia-core:annotation_type": "TimeDomainDetection",
            "ntia-algorithm:detector": "sample_iq",
            "ntia-algorithm:number_of_samples": num_samples,
            "ntia-algorithm:units": "volts",
            "ntia-algorithm:reference": "not referenced",
            "ntia-algorithm:time": time,
            "ntia-algorithm:time_start": 0,
            "ntia-algorithm:time_stop": time[-1],
            "ntia-algorithm:time_step": 1 / sample_rate
        }
        sigmf_md.add_annotation(
            start_index=0, length=num_samples, metadata=time_domain_detection_md
        )

        # Recover the sigan overload flag
        sigan_overload = self.sdr.radio.sigan_overload

        # Check time domain average power versus calibrated compression
        time_domain_avg_power = 10 * np.log10(np.mean(np.abs(data) ** 2))
        time_domain_avg_power += (
            10 * np.log10(1 / (2 * 50)) + 30
        )  # Convert log(V^2) to dBm
        sensor_overload = False
        if self.sdr.radio.sensor_calibration_data["1db_compression_sensor"]:
            sensor_overload = (
                time_domain_avg_power
                > self.sdr.radio.sensor_calibration_data["1db_compression_sensor"]
            )

        # Create SensorAnnotation and add gain setting and overload indicators
        sensor_annotation_md = {
            "ntia-core:annotation_type": "SensorAnnotation",
            "ntia-sensor:overload": sensor_overload or sigan_overload,
            "ntia-sensor:gain_setting_sigan": measurement_params.gain,
        }

        location = get_location()
        if location:
            sensor_annotation_md["core:latitude"] = (location.latitude,)
            sensor_annotation_md["core:longitude"] = location.longitude

        sigmf_md.add_annotation(
            start_index=0, length=num_samples, metadata=sensor_annotation_md
        )

        return sigmf_md

    def configure_sdr(self, measurement_params):
        self.sdr.radio.sample_rate = measurement_params.sample_rate
        self.sdr.radio.tune_frequency(measurement_params.center_frequency)
        self.sdr.radio.gain = measurement_params.gain

    def archive(self, task_result, recording_id, acq_data, sigmf_md):
        from tasks.models import Acquisition

        logger.debug("Storing acquisition in database")

        name = (
            task_result.schedule_entry.name
            + "_"
            + str(task_result.task_id)
            + "_"
            + str(recording_id)
            + ".sigmf-data"
        )

        acquisition = Acquisition(
            task_result=task_result,
            recording_id=recording_id,
            metadata=sigmf_md._metadata,
        )
        acquisition.data.save(name, ContentFile(acq_data))
        acquisition.save()
        logger.debug("Saved new file at {}".format(acquisition.data.path))

    @property
    def description(self):
        """Parameterize and return the module-level docstring."""

        acquisition_plan = ""
        acq_plan_template = "1. Tune to {fc_MHz:.2f} MHz, "
        acq_plan_template += "set gain to {gain} dB, "
        acq_plan_template += "and acquire at {sample_rate_Msps:.2f} Msps "
        acq_plan_template += "for {duration_ms} ms\n"

        total_samples = 0
        for measurement_params in self.measurement_params_list:
            acq_plan_template.format(
                **{
                    "fc_MHz": measurement_params.center_frequency / 1e6,
                    "gain": measurement_params.gain,
                    "sample_rate_Msps": measurement_params.sample_rate / 1e6,
                    "duration_ms": measurement_params.duration_ms,
                }
            )
            total_samples += int(
                measurement_params.duration_ms / 1e6 * measurement_params.sample_rate
            )

        f_low = self.measurement_params_list[0].center_frequency
        f_low_srate = self.measurement_params_list[0].sample_rate
        f_low_edge = (f_low - f_low_srate / 2.0) / 1e6

        f_high = self.measurement_params_list[-1].center_frequency
        f_high_srate = self.measurement_params_list[-1].sample_rate
        f_high_edge = (f_high - f_high_srate / 2.0) / 1e6

        durations = [v.duration_ms for v in self.measurement_params_list]
        min_duration_ms = np.sum(durations)

        filesize_mb = total_samples * 8 / 1e6  # 8 bytes per complex64 sample

        defs = {
            "name": self.name,
            "num_center_frequencies": self.num_center_frequencies,
            "center_frequencies": ", ".join(
                [
                    "{:.2f} MHz".format(param.center_frequency / 1e6)
                    for param in self.measurement_params_list
                ]
            ),
            "acquisition_plan": acquisition_plan,
            "min_duration_ms": min_duration_ms,
            "total_samples": total_samples,
            "filesize_mb": filesize_mb,
        }

        # __doc__ refers to the module docstring at the top of the file
        return __doc__.format(**defs)
